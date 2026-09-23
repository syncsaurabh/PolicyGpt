import { TestBed, fakeAsync, tick } from '@angular/core/testing';
import { Eligibility } from './eligibility';
import { SchemeService } from '../../core/services/scheme.service';
import { provideHttpClient } from '@angular/common/http';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';

describe('Eligibility Component (5-UI Flow)', () => {
  let component: Eligibility;
  let schemeService: SchemeService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [Eligibility],
      providers: [
        provideHttpClient(),
        provideRouter([])
      ]
    });

    component = TestBed.createComponent(Eligibility).componentInstance;
    schemeService = TestBed.inject(SchemeService);
  });

  it('should initialize at Step 1 (form) with pre-filled default values', () => {
    expect(component.currentStep()).toBe('form');
    expect(component.age()).toBe(24);
    expect(component.gender()).toBe('female');
    expect(component.income()).toBe(300000);
    expect(component.occupation()).toBe('student');
    expect(component.state()).toBe('Tamil Nadu');
  });

  it('should validate form and navigate to Step 2 (review)', () => {
    // Valid details
    component.goToReview();
    expect(component.currentStep()).toBe('review');
    expect(component.errorMessage()).toBeNull();

    // Go back to form
    component.backToForm();
    expect(component.currentStep()).toBe('form');

    // Invalid details check
    component.age.set(-5);
    component.goToReview();
    expect(component.currentStep()).toBe('form');
    expect(component.errorMessage()).toContain('valid age');
  });

  it('should progress through Step 3 (analyzing) and transition to Step 4 (results)', fakeAsync(() => {
    spyOn(schemeService, 'checkEligibility').and.returnValue(of({
      eligible_schemes: [
        {
          scheme_id: 201,
          scheme_name: 'Test Scheme',
          eligible: true,
          category: 'Education',
          benefits: 'Test benefits'
        }
      ],
      total_matches: 1
    }));

    component.age.set(24);
    component.income.set(300000);
    component.runAnalysis();

    expect(component.currentStep()).toBe('analyzing');
    expect(component.scanStep()).toBe(1);

    tick(800);
    expect(component.scanStep()).toBe(2);

    tick(900);
    expect(component.scanStep()).toBe(3);

    tick(600);
    expect(component.currentStep()).toBe('results');
    expect(component.results().length).toBeGreaterThan(0);
    expect(component.totalMatches()).toBeGreaterThanOrEqual(1);
  }));

  it('should open and close Step 5 (Scheme Details Modal)', () => {
    const testScheme = {
      scheme_id: 999,
      scheme_name: 'Modal Test Scheme',
      eligible: true,
      category: 'Scholarships',
      benefits: 'Full scholarship grant',
      matched_rules: ['Rule 1 verified', 'Rule 2 verified']
    };

    component.openSchemeDetails(testScheme);
    expect(component.showModal()).toBe(true);
    expect(component.selectedScheme()?.scheme_name).toBe('Modal Test Scheme');

    component.closeSchemeModal();
    expect(component.showModal()).toBe(false);
    expect(component.selectedScheme()).toBeNull();
  });

  it('should allow restarting check to return to Step 1', () => {
    component.currentStep.set('results');
    component.restartCheck();
    expect(component.currentStep()).toBe('form');
  });
});
