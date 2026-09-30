import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';

import { ApiError, Reading, ReadingRequest } from './reading.models';
import { API_BASE_URL } from './api-config';

@Injectable({ providedIn: 'root' })
export class ReadingService {
  private readonly http = inject(HttpClient);

  getReading(request: ReadingRequest): Observable<Reading> {
    return this.http
      .post<Reading>(`${API_BASE_URL}/api/reading`, request)
      .pipe(catchError((error) => throwError(() => this.toApiError(error))));
  }

  /**
   * Collapse anything HttpClient can throw into the one shape the UI knows.
   *
   * The backend already flattens its validation errors to {message, field},
   * so the work here is the cases that never reach the backend at all: a
   * cold Render instance, a dropped connection, a CORS failure. Those arrive
   * as status 0 and would otherwise render as an empty message.
   */
  private toApiError(error: HttpErrorResponse): ApiError {
    if (error.status === 0) {
      return {
        message:
          'Could not reach the calculation service. It may be waking up from ' +
          'idle, which takes up to a minute on a free instance. Please try again.',
        field: null,
      };
    }

    const body = error.error as Partial<ApiError> | null;
    if (body && typeof body.message === 'string' && body.message) {
      return { message: body.message, field: body.field ?? null };
    }

    return {
      message: 'Something went wrong while calculating. Please try again.',
      field: null,
    };
  }
}
