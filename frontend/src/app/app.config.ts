import { ApplicationConfig, LOCALE_ID, isDevMode } from '@angular/core';
import { DATE_PIPE_DEFAULT_OPTIONS } from '@angular/common';
import { provideRouter, withViewTransitions } from '@angular/router';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { provideServiceWorker } from '@angular/service-worker';
import { routes } from './app.routes';
import { apiAuthInterceptor } from './core/interceptors/api-auth.interceptor';
import { adminAuthErrorInterceptor } from './core/interceptors/admin-auth-error.interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    { provide: LOCALE_ID, useValue: 'es-BO' },
    { provide: DATE_PIPE_DEFAULT_OPTIONS, useValue: { timezone: '-0400' } },
    provideRouter(routes, withViewTransitions()),
    provideHttpClient(withInterceptors([apiAuthInterceptor, adminAuthErrorInterceptor])),
    provideAnimationsAsync(),
    provideServiceWorker('ngsw-worker.js', {
      enabled: !isDevMode(),
      registrationStrategy: 'registerWhenStable:30000',
    }),
  ],
};
