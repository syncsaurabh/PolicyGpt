import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { Policies } from './policies';
import { Policy } from './services/policy';

describe('Policies Component', () => {
  let component: Policies;
  let fixture: ComponentFixture<Policies>;
  let policyService: Policy;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Policies],
      providers: [
        provideRouter([]),
        Policy
      ]
    }).compileComponents();

    policyService = TestBed.inject(Policy);
    policyService.resetToDefaults();
    fixture = TestBed.createComponent(Policies);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create the component', () => {
    expect(component).toBeTruthy();
  });

  it('should render page title "Policy Management"', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const title = compiled.querySelector('.page-title')?.textContent;
    expect(title).toContain('Policy Management');
  });

  it('should filter policies by category', () => {
    component.selectCategory('Education');
    fixture.detectChanges();
    const filtered = component['filteredPolicies']();
    expect(filtered.every(p => p.category === 'Education')).toBe(true);
  });

  it('should filter policies by search query', () => {
    component['searchQuery'].set('PM-KISAN');
    component.onSearchChange();
    fixture.detectChanges();
    const filtered = component['filteredPolicies']();
    expect(filtered.length).toBeGreaterThan(0);
    expect(filtered[0].id).toBe('POL-002');
  });
});
