import { ApplicationConfig, LOCALE_ID } from '@angular/core';
import { DATE_PIPE_DEFAULT_OPTIONS } from '@angular/common';
import { provideRouter, withViewTransitions } from '@angular/router';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { routes } from './app.routes';
import { apiAuthInterceptor } from './core/interceptors/api-auth.interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    { provide: LOCALE_ID, useValue: 'es-BO' },
    { provide: DATE_PIPE_DEFAULT_OPTIONS, useValue: { timezone: '-0400' } },
    provideRouter(routes, withViewTransitions()),
    provideHttpClient(withInterceptors([apiAuthInterceptor])),
    provideAnimationsAsync(),
  ],
};
