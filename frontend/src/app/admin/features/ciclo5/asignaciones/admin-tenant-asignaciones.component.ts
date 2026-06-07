import {
  Component,
  inject,
  OnInit,
  ChangeDetectionStrategy,
  ChangeDetectorRef,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { forkJoin } from 'rxjs';
import { AdminApiService } from '../../../../core/services/admin-api.service';
import type {
  AssignmentResultDto,
  TenantDto,
  TenantMembersDto,
  UsuarioListDto,
  TallerDto,
} from '../../../../core/models/admin-api.models';

type Tab = 'usuarios' | 'talleres' | 'tecnicos';

@Component({
  selector: 'app-admin-tenant-asignaciones',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './admin-tenant-asignaciones.component.html',
  styleUrl: './admin-tenant-asignaciones.component.scss',
})
export class AdminTenantAsignacionesComponent implements OnInit {
  private readonly api = inject(AdminApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly cdr = inject(ChangeDetectorRef);

  tenantId!: number;
  tenant: TenantDto | null = null;
  members: TenantMembersDto | null = null;

  allUsuarios: UsuarioListDto[] = [];
  allTalleres: TallerDto[] = [];

  loading = true;
  error: string | null = null;
  busy = false;
  successMsg: string | null = null;

  activeTab: Tab = 'usuarios';

  // Selección para asignar
  selectedUserIds: Set<number> = new Set();
  selectedWorkshopIds: Set<number> = new Set();

  ngOnInit(): void {
    this.tenantId = Number(this.route.snapshot.paramMap.get('id'));
    this.reload();
  }

  reload(): void {
    this.loading = true;
    this.error = null;
    forkJoin({
      tenant: this.api.getTenant(this.tenantId),
      members: this.api.getTenantMembers(this.tenantId),
      usuarios: this.api.listUsuarios(),
      talleres: this.api.listTalleres(),
    }).subscribe({
      next: ({ tenant, members, usuarios, talleres }) => {
        this.tenant = tenant;
        this.members = members;
        this.allUsuarios = usuarios;
        this.allTalleres = talleres;
        this.loading = false;
        this.cdr.markForCheck();
      },
      error: () => {
        this.loading = false;
        this.error = 'No se pudo cargar la información del tenant.';
        this.cdr.markForCheck();
      },
    });
  }

  get memberUserIds(): Set<number> {
    return new Set(this.members?.usuarios.map((u) => u.id) ?? []);
  }

  get memberWorkshopIds(): Set<number> {
    return new Set(this.members?.talleres.map((t) => t.id) ?? []);
  }

  get availableUsuarios(): UsuarioListDto[] {
    const assigned = this.memberUserIds;
    return this.allUsuarios.filter((u) => !assigned.has(u.id));
  }

  get availableTalleres(): TallerDto[] {
    const assigned = this.memberWorkshopIds;
    return this.allTalleres.filter((t) => !assigned.has(t.id));
  }

  toggleUser(id: number): void {
    if (this.selectedUserIds.has(id)) {
      this.selectedUserIds.delete(id);
    } else {
      this.selectedUserIds.add(id);
    }
    this.cdr.markForCheck();
  }

  toggleWorkshop(id: number): void {
    if (this.selectedWorkshopIds.has(id)) {
      this.selectedWorkshopIds.delete(id);
    } else {
      this.selectedWorkshopIds.add(id);
    }
    this.cdr.markForCheck();
  }

  assignUsers(): void {
    if (this.selectedUserIds.size === 0) return;
    this.busy = true;
    this.error = null;
    this.api.assignUsersToTenant(this.tenantId, [...this.selectedUserIds]).subscribe({
      next: (r) => this._handleAssignResult(r),
      error: (err) => this._handleAssignError(err),
    });
  }

  assignWorkshops(): void {
    if (this.selectedWorkshopIds.size === 0) return;
    this.busy = true;
    this.error = null;
    this.api.assignWorkshopsToTenant(this.tenantId, [...this.selectedWorkshopIds]).subscribe({
      next: (r) => this._handleAssignResult(r),
      error: (err) => this._handleAssignError(err),
    });
  }

  private _handleAssignResult(r: AssignmentResultDto): void {
    this.busy = false;
    this.selectedUserIds.clear();
    this.selectedWorkshopIds.clear();
    this.successMsg = r.message;
    setTimeout(() => { this.successMsg = null; this.cdr.markForCheck(); }, 4000);
    this.reload();
  }

  private _handleAssignError(err: unknown): void {
    this.busy = false;
    const e = err as { error?: { detail?: string } };
    this.error = e?.error?.detail ?? 'No se pudo completar la asignación.';
    this.cdr.markForCheck();
  }

  setTab(tab: Tab): void {
    this.activeTab = tab;
    this.cdr.markForCheck();
  }
}
