/** Mirrors the backend response in app/models.py. */

export interface MethodResult {
  id: string;
  label: string;
  result: string;
  detail: string;
  basis: string;
  notes: string[];
  scores: Record<string, number>;
}

export interface TraitRow {
  trait: string;
  scores: Record<string, number>;
  agreeing: string[];
  n: number;
  confidence: number;
}

export interface Reading {
  full_name: string;
  date_of_birth: string;
  time_of_birth: string;
  methods: MethodResult[];
  traits: TraitRow[];
  summary: string;
  summary_source: 'model' | 'template';
  assumptions: string[];
}

export interface ReadingRequest {
  full_name: string;
  date_of_birth: string;
  time_of_birth: string;
}

/** The backend flattens every validation failure to this shape. */
export interface ApiError {
  message: string;
  field: string | null;
}

/** The brief's agreement threshold, needed to highlight it in the matrix. */
export const AGREEMENT_THRESHOLD = 7;
