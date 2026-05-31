import { registerLocaleData } from '@angular/common';
import { bootstrapApplication } from '@angular/platform-browser';
import localeEsBo from '@angular/common/locales/es-BO';
import { appConfig } from './app/app.config';
import { AppComponent } from './app/app.component';

registerLocaleData(localeEsBo);

bootstrapApplication(AppComponent, appConfig)
  .catch((err) => console.error(err));
