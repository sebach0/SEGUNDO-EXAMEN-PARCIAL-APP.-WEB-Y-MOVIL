import { Component } from '@angular/core';
import { AdminDashboardComponent } from '../dashboard/admin-dashboard.component';

@Component({
  selector: 'app-admin-finanzas',
  standalone: true,
  imports: [AdminDashboardComponent],
  templateUrl: './admin-finanzas.component.html',
  styleUrl: './admin-finanzas.component.scss',
})
export class AdminFinanzasComponent {}

