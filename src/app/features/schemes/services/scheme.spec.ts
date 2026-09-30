import { TestBed } from '@angular/core/testing';
import { Scheme } from './scheme';
import { INITIAL_SCHEMES } from '../../../models/scheme.model';

describe('Scheme Service', () => {
  let service: Scheme;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({});
    service = TestBed.inject(Scheme);
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should load initial schemes data', () => {
    const all = service.getAll();
    expect(all.length).toBeGreaterThanOrEqual(10);
    expect(service.totalSchemes()).toBe(all.length);
  });

  it('should find a scheme by ID', () => {
    const found = service.getById('SCH-001');
    expect(found).toBeDefined();
    expect(found?.name).toContain('PM Kisan');
  });

  it('should filter schemes by category', () => {
    const healthcare = service.filterAndSearch('', 'Healthcare');
    expect(healthcare.length).toBeGreaterThan(0);
    healthcare.forEach(s => expect(s.category).toBe('Healthcare'));
  });

  it('should filter schemes by state', () => {
    const maharashtra = service.filterAndSearch('', 'All', 'Maharashtra');
    expect(maharashtra.length).toBeGreaterThan(0);
    maharashtra.forEach(s => expect(s.state).toBe('Maharashtra'));
  });

  it('should filter schemes by search query', () => {
    const results = service.filterAndSearch('Ayushman');
    expect(results.length).toBeGreaterThan(0);
    expect(results[0].name).toContain('Ayushman');
  });

  it('should create a new scheme', () => {
    const initialCount = service.totalSchemes();
    const created = service.create({
      id: 'SCH-999',
      name: 'New Test Welfare Scheme',
      description: 'Test description for newly created scheme.',
      category: 'Student Schemes',
      ministry: 'Ministry of Education',
      department: 'Department of Higher Education',
      state: 'Central / All India',
      benefits: 'Full tuition reimbursement',
      eligibilityCriteria: 'Enrolled college students',
      applicationProcess: 'Apply online',
      applicationUrl: 'https://test-scheme.gov.in',
      startDate: '01 Jan 2026',
      endDate: '31 Dec 2027',
      status: 'Active',
      tags: ['Test', 'Education']
    });

    expect(created.id).toBe('SCH-999');
    expect(service.totalSchemes()).toBe(initialCount + 1);
    expect(service.getById('SCH-999')).toBeDefined();
  });

  it('should update an existing scheme', () => {
    const updated = service.update('SCH-001', {
      benefits: 'Updated direct financial benefit of ₹8,000 annually.'
    });

    expect(updated).toBeDefined();
    expect(updated?.benefits).toContain('₹8,000');
    expect(service.getById('SCH-001')?.benefits).toContain('₹8,000');
  });

  it('should archive and restore a scheme', () => {
    const archived = service.archive('SCH-001');
    expect(archived?.status).toBe('Archived');
    expect(service.getById('SCH-001')?.status).toBe('Archived');

    const restored = service.restore('SCH-001');
    expect(restored?.status).toBe('Active');
    expect(service.getById('SCH-001')?.status).toBe('Active');
  });

  it('should delete a scheme permanently', () => {
    const initialCount = service.totalSchemes();
    const deleted = service.delete('SCH-002');
    expect(deleted).toBe(true);
    expect(service.totalSchemes()).toBe(initialCount - 1);
    expect(service.getById('SCH-002')).toBeUndefined();
  });
});
