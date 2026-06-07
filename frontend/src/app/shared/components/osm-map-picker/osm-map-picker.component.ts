import {
  AfterViewInit,
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  ElementRef,
  EventEmitter,
  Input,
  NgZone,
  OnChanges,
  OnDestroy,
  Output,
  SimpleChanges,
  ViewChild,
  inject,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import * as L from 'leaflet';

export interface MapLocation {
  lat: number;
  lng: number;
}

/** Centro por defecto: Santa Cruz de la Sierra, Bolivia */
const DEFAULT_CENTER: L.LatLngExpression = [-17.783, -63.182];
const DEFAULT_ZOOM = 13;

@Component({
  selector: 'app-osm-map-picker',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule],
  templateUrl: './osm-map-picker.component.html',
  styleUrl: './osm-map-picker.component.scss',
})
export class OsmMapPickerComponent implements AfterViewInit, OnChanges, OnDestroy {
  @ViewChild('mapHost', { static: true }) mapHost!: ElementRef<HTMLDivElement>;

  @Input() latitude: number | null = null;
  @Input() longitude: number | null = null;
  @Input() readonly = false;
  @Input() showGeolocate = true;
  @Input() height = '300px';
  @Input() primaryLabel = 'Taller';
  @Input() secondaryLabel = 'Incidente';
  @Input() secondaryLat: number | null = null;
  @Input() secondaryLng: number | null = null;

  @Output() locationChange = new EventEmitter<MapLocation>();

  locating = false;
  geoError: string | null = null;

  private readonly zone = inject(NgZone);
  private readonly cdr  = inject(ChangeDetectorRef);

  private map: L.Map | null = null;
  private primaryMarker: L.Marker | null = null;
  private secondaryMarker: L.Marker | null = null;
  private routeLine: L.Polyline | null = null;
  private resizeObs: ResizeObserver | null = null;
  private ready = false;

  ngAfterViewInit(): void {
    /**
     * Doble requestAnimationFrame:
     *   1er RAF → Angular terminó de aplicar todos los bindings ([style.height], etc.)
     *   2do RAF → el browser calculó el layout real (offsetWidth/offsetHeight correctos)
     * Recién entonces Leaflet mide el contenedor y renderiza bien.
     */
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        this.zone.runOutsideAngular(() => {
          this.initMap();
          this.resizeObs = new ResizeObserver(() => {
            this.map?.invalidateSize();
          });
          this.resizeObs.observe(this.mapHost.nativeElement);
        });
        this.ready = true;
        this.syncMarkers();
      });
    });
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (!this.ready) return;
    if (
      changes['latitude'] ||
      changes['longitude'] ||
      changes['secondaryLat'] ||
      changes['secondaryLng'] ||
      changes['readonly']
    ) {
      this.syncMarkers();
    }
  }

  ngOnDestroy(): void {
    this.resizeObs?.disconnect();
    this.map?.remove();
    this.map = null;
  }

  useMyLocation(): void {
    if (this.readonly || !navigator.geolocation) {
      this.geoError = 'Geolocalización no disponible en este navegador.';
      this.cdr.markForCheck();
      return;
    }
    this.locating = true;
    this.geoError = null;
    this.cdr.markForCheck();

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        this.zone.run(() => {
          this.locating = false;
          this.setPrimary(pos.coords.latitude, pos.coords.longitude, true);
        });
      },
      () => {
        this.zone.run(() => {
          this.locating = false;
          this.geoError = 'No se pudo obtener tu ubicación. Hacé clic en el mapa para marcar.';
          this.cdr.markForCheck();
        });
      },
      { enableHighAccuracy: true, timeout: 12000 },
    );
  }

  private initMap(): void {
    const el = this.mapHost.nativeElement;

    this.map = L.map(el, {
      zoomControl: true,
    }).setView(DEFAULT_CENTER, DEFAULT_ZOOM);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    }).addTo(this.map);

    if (!this.readonly) {
      this.map.on('click', (e: L.LeafletMouseEvent) => {
        this.zone.run(() => {
          this.setPrimary(e.latlng.lat, e.latlng.lng, true);
        });
      });
    }

    // Un último invalidateSize tras las animaciones de apertura de la card
    setTimeout(() => this.map?.invalidateSize(), 300);
  }

  private setPrimary(lat: number, lng: number, emit: boolean): void {
    this.latitude = lat;
    this.longitude = lng;
    this.syncMarkers();
    this.cdr.markForCheck();
    if (emit) {
      this.locationChange.emit({ lat, lng });
    }
  }

  private syncMarkers(): void {
    if (!this.map) return;

    this.primaryMarker?.remove();
    this.secondaryMarker?.remove();
    this.routeLine?.remove();
    this.primaryMarker = null;
    this.secondaryMarker = null;
    this.routeLine = null;

    const bounds: L.LatLngExpression[] = [];

    if (this.latitude != null && this.longitude != null) {
      const pos: L.LatLngExpression = [this.latitude, this.longitude];
      bounds.push(pos);
      this.primaryMarker = L.marker(pos, {
        icon: this.pinIcon('#2563eb'),
        title: this.primaryLabel,
        draggable: !this.readonly,
      }).addTo(this.map);
      this.primaryMarker.bindPopup(`<strong>${this.primaryLabel}</strong>`);

      if (!this.readonly) {
        this.primaryMarker.on('dragend', (e) => {
          const latlng = (e.target as L.Marker).getLatLng();
          this.zone.run(() => {
            this.setPrimary(latlng.lat, latlng.lng, true);
          });
        });
      }
    }

    if (this.secondaryLat != null && this.secondaryLng != null) {
      const pos: L.LatLngExpression = [this.secondaryLat, this.secondaryLng];
      bounds.push(pos);
      this.secondaryMarker = L.marker(pos, {
        icon: this.pinIcon('#dc2626'),
        title: this.secondaryLabel,
      }).addTo(this.map);
      this.secondaryMarker.bindPopup(`<strong>${this.secondaryLabel}</strong>`);
    }

    if (
      this.latitude != null &&
      this.longitude != null &&
      this.secondaryLat != null &&
      this.secondaryLng != null
    ) {
      this.routeLine = L.polyline(
        [[this.latitude, this.longitude], [this.secondaryLat, this.secondaryLng]],
        { color: '#64748b', weight: 3, dashArray: '8 6', opacity: 0.85 },
      ).addTo(this.map);
    }

    if (bounds.length === 1) {
      this.map.setView(bounds[0], 15);
    } else if (bounds.length > 1) {
      this.map.fitBounds(L.latLngBounds(bounds), { padding: [36, 36], maxZoom: 15 });
    } else {
      this.map.setView(DEFAULT_CENTER, DEFAULT_ZOOM);
    }
  }

  private pinIcon(color: string): L.DivIcon {
    return L.divIcon({
      className: 'osm-map-picker__pin-wrap',
      html: `<span class="osm-map-picker__pin" style="background:${color}"></span>`,
      iconSize: [20, 20],
      iconAnchor: [10, 20],
      popupAnchor: [0, -22],
    });
  }
}
