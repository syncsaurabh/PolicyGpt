import { TestBed } from '@angular/core/testing';
import { Policy } from './policy';

describe('Policy Service', () => {
  let service: Policy;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(Policy);
    service.resetToDefaults();
  });

  it('should be created and contain initial policies', () => {
    expect(service).toBeTruthy();
    expect(service.getAll().length).toBeGreaterThan(0);
    expect(service.totalPolicies()).toBeGreaterThan(0);
  });

  it('should find policy by ID', () => {
    const policy = service.getById('POL-001');
    expect(policy).toBeTruthy();
    expect(policy?.name).toContain('National Education Policy');
  });

  it('should create a new policy and persist it', () => {
    const initialCount = service.getAll().length;
    const created = service.create({
      id: 'POL-TEST-999',
      name: 'Test Innovation Policy',
      description: 'Test description',
      ministry: 'Ministry of Electronics & IT',
      department: 'Digital Governance Division',
      category: 'Finance',
      sector: 'Technology',
      publicationDate: '11 Sep 2026',
      effectiveDate: '01 Oct 2026',
      tags: ['Innovation', 'Tech'],
      document: {
        name: 'test_innovation.pdf',
        size: '1.0 MB',
        type: 'PDF'
      },
      status: 'Draft'
    });

    expect(created.id).toBe('POL-TEST-999');
    expect(service.getAll().length).toBe(initialCount + 1);
    expect(service.getById('POL-TEST-999')).toBeTruthy();
  });

  it('should update an existing policy', () => {
    const updated = service.update('POL-001', {
      name: 'National Education Policy 2020 (Amended)'
    });
    expect(updated?.name).toBe('National Education Policy 2020 (Amended)');
    expect(service.getById('POL-001')?.name).toBe('National Education Policy 2020 (Amended)');
  });

  it('should submit policy for review and update status', () => {
    const submitted = service.submitForReview('POL-004');
    expect(submitted?.status).toBe('Under Review');
    expect(submitted?.submittedAt).toBeTruthy();
    expect(service.getById('POL-004')?.status).toBe('Under Review');
  });

  it('should archive policy and update status', () => {
    const archived = service.archive('POL-001');
    expect(archived?.status).toBe('Archived');
    expect(service.getById('POL-001')?.status).toBe('Archived');
  });

  it('should filter and search policies correctly', () => {
    const educationPolicies = service.filterAndSearch('', 'Education');
    expect(educationPolicies.every(p => p.category === 'Education')).toBe(true);

    const searchResult = service.filterAndSearch('Health', 'All');
    expect(searchResult.some(p => p.name.includes('Health'))).toBe(true);
  });
});
