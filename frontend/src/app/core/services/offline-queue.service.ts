import { Injectable } from '@angular/core';
import type { OfflineEvent, SyncLocalStatus } from '../models/ciclo4.models';

/**
 * OfflineQueueService — Ciclo 4
 * Persiste eventos capturados sin conexión en IndexedDB.
 *
 * ¿Por qué IndexedDB y no localStorage?
 * localStorage tiene límite de ~5MB y es síncrono (bloquea el hilo principal).
 * IndexedDB es asíncrono, soporta objetos complejos y tiene límites mucho mayores.
 *
 * Estructura de la BD:
 *   DB: ev_offline_queue (v1)
 *   Store: offline_events  (keyPath: client_uuid)
 */

const DB_NAME = 'ev_offline_queue';
const DB_VERSION = 1;
const STORE_NAME = 'offline_events';

@Injectable({ providedIn: 'root' })
export class OfflineQueueService {
  private db: IDBDatabase | null = null;
  private dbReady: Promise<IDBDatabase>;

  constructor() {
    this.dbReady = this._openDB();
  }

  // ── Apertura y setup de IndexedDB ────────────────────────────────────────

  private _openDB(): Promise<IDBDatabase> {
    return new Promise((resolve, reject) => {
      const req = indexedDB.open(DB_NAME, DB_VERSION);

      req.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;
        if (!db.objectStoreNames.contains(STORE_NAME)) {
          db.createObjectStore(STORE_NAME, { keyPath: 'client_uuid' });
        }
      };

      req.onsuccess = (event) => {
        this.db = (event.target as IDBOpenDBRequest).result;
        resolve(this.db);
      };

      req.onerror = (event) => {
        reject((event.target as IDBOpenDBRequest).error);
      };
    });
  }

  private async _getDB(): Promise<IDBDatabase> {
    return this.db ?? (await this.dbReady);
  }

  // ── Generación de UUID (anti-duplicado) ───────────────────────────────────

  /**
   * Genera un UUID v4 para identificar cada registro offline.
   * Usa crypto.randomUUID si está disponible (navegadores modernos),
   * fallback manual para entornos que no lo soportan.
   */
  generateClientUuid(): string {
    if (typeof crypto !== 'undefined' && crypto.randomUUID) {
      return crypto.randomUUID();
    }
    // Fallback simple RFC 4122 v4
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
      const r = (Math.random() * 16) | 0;
      return (c === 'x' ? r : (r & 0x3) | 0x8).toString(16);
    });
  }

  // ── CRUD ──────────────────────────────────────────────────────────────────

  /** Agrega un evento offline. Si el client_uuid ya existe, no duplica. */
  async addOfflineEvent(event: Omit<OfflineEvent, '_intentos' | '_ultimo_error'>): Promise<void> {
    const db = await this._getDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, 'readwrite');
      const store = tx.objectStore(STORE_NAME);

      // Verifica primero si ya existe el client_uuid (anti-duplicado local)
      const getReq = store.get(event.client_uuid);
      getReq.onsuccess = () => {
        if (getReq.result) {
          // Ya existe — no duplicar
          resolve();
          return;
        }
        const full: OfflineEvent = {
          ...event,
          _intentos: 0,
          _ultimo_error: null,
        };
        const putReq = store.put(full);
        putReq.onsuccess = () => resolve();
        putReq.onerror = (e) => reject((e.target as IDBRequest).error);
      };
      getReq.onerror = (e) => reject((e.target as IDBRequest).error);
    });
  }

  /** Devuelve todos los eventos con estado pendiente. */
  async getPendingEvents(): Promise<OfflineEvent[]> {
    const db = await this._getDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, 'readonly');
      const store = tx.objectStore(STORE_NAME);
      const req = store.getAll();
      req.onsuccess = () => {
        const all: OfflineEvent[] = req.result as OfflineEvent[];
        resolve(all.filter((e) => e._estado_local === 'pendiente' || e._estado_local === 'error'));
      };
      req.onerror = (e) => reject((e.target as IDBRequest).error);
    });
  }

  /** Devuelve todos los eventos (para la vista de estado de sincronización). */
  async getAllEvents(): Promise<OfflineEvent[]> {
    const db = await this._getDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, 'readonly');
      const store = tx.objectStore(STORE_NAME);
      const req = store.getAll();
      req.onsuccess = () => resolve(req.result as OfflineEvent[]);
      req.onerror = (e) => reject((e.target as IDBRequest).error);
    });
  }

  async markAsSent(clientUuid: string): Promise<void> {
    await this._updateStatus(clientUuid, 'enviado');
  }

  async markAsSynced(clientUuid: string): Promise<void> {
    await this._updateStatus(clientUuid, 'sincronizado');
  }

  async markAsError(clientUuid: string, error: string): Promise<void> {
    const db = await this._getDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, 'readwrite');
      const store = tx.objectStore(STORE_NAME);
      const getReq = store.get(clientUuid);
      getReq.onsuccess = () => {
        const record: OfflineEvent | undefined = getReq.result as OfflineEvent | undefined;
        if (!record) { resolve(); return; }
        record._estado_local = 'error';
        record._intentos = (record._intentos ?? 0) + 1;
        record._ultimo_error = error;
        const putReq = store.put(record);
        putReq.onsuccess = () => resolve();
        putReq.onerror = (e) => reject((e.target as IDBRequest).error);
      };
      getReq.onerror = (e) => reject((e.target as IDBRequest).error);
    });
  }

  private async _updateStatus(clientUuid: string, status: SyncLocalStatus): Promise<void> {
    const db = await this._getDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, 'readwrite');
      const store = tx.objectStore(STORE_NAME);
      const getReq = store.get(clientUuid);
      getReq.onsuccess = () => {
        const record: OfflineEvent | undefined = getReq.result as OfflineEvent | undefined;
        if (!record) { resolve(); return; }
        record._estado_local = status;
        if (status === 'enviado' || status === 'sincronizado') {
          record._ultimo_error = null;
        }
        const putReq = store.put(record);
        putReq.onsuccess = () => resolve();
        putReq.onerror = (e) => reject((e.target as IDBRequest).error);
      };
      getReq.onerror = (e) => reject((e.target as IDBRequest).error);
    });
  }
}
