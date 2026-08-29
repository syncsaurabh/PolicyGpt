import { TestBed } from '@angular/core/testing';
import { Scheme } from './scheme';

describe('Scheme', () => {
  let service: Scheme;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(Scheme);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
