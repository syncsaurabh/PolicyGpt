import { Component, inject, signal, computed, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { CitizenHeaderComponent } from '../citizen-dashboard/components/citizen-header/citizen-header.component';
import { CitizenFooterComponent } from '../citizen-dashboard/components/citizen-footer/citizen-footer.component';
import { PolicyService } from '../../../core/services/policy.service';
import { DashboardService } from '../../../core/services/dashboard.service';
import { Auth } from '../../../core/services/auth';
import { PolicyReadDto } from '../../../models/policy.model';

export interface PublicPolicyCard {
  id: string | number;
  title: string;
  category: string;
  description: string;
  eligibility: string;
  benefits: string;
  state?: string;
  ministry?: string;
  targetBeneficiary?: string;
  bookmarked?: boolean;
}

@Component({
  selector: 'app-public-policies',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, CitizenHeaderComponent, CitizenFooterComponent],
  templateUrl: './public-policies.component.html',
  styleUrl: './public-policies.component.css'
})
export class PublicPoliciesComponent implements OnInit {
  private readonly policyService = inject(PolicyService);
  private readonly dashboardService = inject(DashboardService);
  private readonly auth = inject(Auth);
  private readonly router = inject(Router);

  searchQuery = signal<string>('');
  searchInputModel = '';
  selectedCategory = signal<string>('All');
  selectedEligibility = signal<string>('All');
  selectedState = signal<string>('All');
  selectedMinistry = signal<string>('All');

  isLoading = signal<boolean>(false);
  policiesList = signal<PublicPolicyCard[]>([]);

  readonly categories = [
    'All',
    'Education',
    'Employment',
    'Agriculture',
    'Healthcare',
    'Women',
    'Housing'
  ];

  readonly eligibilityOptions = [
    'All',
    'Students',
    'Farmers',
    'Families',
    'Senior Citizens'
  ];

  readonly states = [
    'All',
    'Central / All India',
    'Maharashtra',
    'Delhi',
    'Karnataka',
    'Uttar Pradesh',
    'Tamil Nadu',
    'Gujarat',
    'Rajasthan'
  ];

  readonly ministries = [
    'All',
    'Ministry of Agriculture & Farmers Welfare',
    'Ministry of Health and Family Welfare',
    'Ministry of Education',
    'Ministry of Housing and Urban Affairs',
    'Ministry of Finance',
    'Ministry of Women and Child Development'
  ];

  // Default initial public policy catalogue matching design
  private readonly fallbackPolicies: PublicPolicyCard[] = [
    {
      id: 'pm-kisan',
      title: 'PM-KISAN',
      category: 'Agriculture',
      description: 'Financial support for eligible farmers to support their agricultural needs',
      eligibility: 'Eligible farmers',
      benefits: 'Financial assistance',
      state: 'Central / All India',
      ministry: 'Ministry of Agriculture & Farmers Welfare',
      targetBeneficiary: 'Farmers'
    },
    {
      id: 'ayushman-bharat',
      title: 'Ayushman Bharat',
      category: 'Healthcare',
      description: 'Healthcare support and financial...',
      eligibility: 'Eligible families',
      benefits: 'Healthcare coverage',
      state: 'Central / All India',
      ministry: 'Ministry of Health and Family Welfare',
      targetBeneficiary: 'Families'
    },
    {
      id: 'national-scholarship-portal',
      title: 'National Scholarship Portal',
      category: 'Education',
      description: 'A platform to access and apply...',
      eligibility: 'Eligible students',
      benefits: 'Scholarship assistance',
      state: 'Central / All India',
      ministry: 'Ministry of Education',
      targetBeneficiary: 'Students'
    },
    {
      id: 'pm-awas-yojana',
      title: 'Pradhan Mantri Awas Yojana (PMAY)',
      category: 'Housing',
      description: 'Credit-linked subsidy and financial assistance for pucca house construction in urban and rural areas.',
      eligibility: 'Eligible families without pucca house',
      benefits: 'Housing financial subsidy up to ₹2.67 Lakh',
      state: 'Central / All India',
      ministry: 'Ministry of Housing and Urban Affairs',
      targetBeneficiary: 'Families'
    },
    {
      id: 'pm-mudra-yojana',
      title: 'Pradhan Mantri Mudra Yojana (PMMY)',
      category: 'Employment',
      description: 'Collateral-free institutional credit to micro and small enterprises for business expansion.',
      eligibility: 'Micro-entrepreneurs and self-employed youth',
      benefits: 'Collateral-free credit loans up to ₹10 Lakh',
      state: 'Central / All India',
      ministry: 'Ministry of Finance',
      targetBeneficiary: 'Students'
    },
    {
      id: 'sukanya-samriddhi-yojana',
      title: 'Sukanya Samriddhi Yojana (SSY)',
      category: 'Women',
      description: 'Government-backed savings scheme aimed at securing the financial future and higher education of girl children.',
      eligibility: 'Parents/guardians of girl child below 10 years',
      benefits: 'High guaranteed interest rate (8.2%) with tax benefits',
      state: 'Central / All India',
      ministry: 'Ministry of Women and Child Development',
      targetBeneficiary: 'Families'
    }
  ];

  ngOnInit(): void {
    this.fetchPolicies();
  }

  fetchPolicies(): void {
    this.isLoading.set(true);
    const localBookmarks = this.getLocalBookmarks();

    this.policyService.listPolicies().subscribe({
      next: (res) => {
        this.isLoading.set(false);
        const results = res?.results;
        if (results && results.length > 0) {
          const mapped: PublicPolicyCard[] = results.map((dto: PolicyReadDto) => ({
            id: dto.id,
            title: dto.title || 'Government Policy',
            category: dto.category || 'General',
            description: dto.description || 'Comprehensive government policy initiative supporting national welfare.',
            eligibility: dto.sector || 'Eligible citizens and designated beneficiary groups',
            benefits: 'Structured policy protections, standards, and welfare assistance',
            state: dto.state || 'Central / All India',
            ministry: dto.ministry || dto.department || 'Government of India',
            targetBeneficiary: dto.sector || 'Families',
            bookmarked: localBookmarks.has(String(dto.id))
          }));

          const combined = [...mapped];
          for (const fb of this.fallbackPolicies) {
            if (!combined.some(c => String(c.id).toLowerCase() === String(fb.id).toLowerCase() || c.title.toLowerCase() === fb.title.toLowerCase())) {
              combined.push({
                ...fb,
                bookmarked: localBookmarks.has(String(fb.id))
              });
            }
          }
          this.policiesList.set(combined);
        } else {
          this.policiesList.set(this.fallbackPolicies.map(fb => ({
            ...fb,
            bookmarked: localBookmarks.has(String(fb.id))
          })));
        }

        // Sync with backend if user is authenticated citizen
        if (this.auth.isAuthenticated()) {
          this.syncBackendBookmarks();
        }
      },
      error: () => {
        this.isLoading.set(false);
        this.policiesList.set(this.fallbackPolicies.map(fb => ({
          ...fb,
          bookmarked: localBookmarks.has(String(fb.id))
        })));
        if (this.auth.isAuthenticated()) {
          this.syncBackendBookmarks();
        }
      }
    });
  }

  private getLocalBookmarks(): Set<string> {
    try {
      const stored = localStorage.getItem('policy_bookmarks');
      return stored ? new Set(JSON.parse(stored)) : new Set();
    } catch {
      return new Set();
    }
  }

  private saveLocalBookmarks(bookmarks: Set<string>): void {
    try {
      localStorage.setItem('policy_bookmarks', JSON.stringify(Array.from(bookmarks)));
    } catch {}
  }

  private syncBackendBookmarks(): void {
    this.dashboardService.getCitizenDashboard().subscribe({
      next: (dash) => {
        if (dash.saved_policies) {
          const backendIds = new Set<string>();
          dash.saved_policies.forEach(sp => {
            if (sp.policy_id) backendIds.add(String(sp.policy_id));
            if (sp.id) backendIds.add(String(sp.id));
          });
          const localSet = this.getLocalBookmarks();
          backendIds.forEach(id => localSet.add(id));
          this.saveLocalBookmarks(localSet);

          this.policiesList.update(list =>
            list.map(p => ({
              ...p,
              bookmarked: backendIds.has(String(p.id)) || localSet.has(String(p.id))
            }))
          );
        }
      },
      error: () => {}
    });
  }

  onSearchSubmit(): void {
    this.searchQuery.set(this.searchInputModel.trim());
  }

  setCategory(cat: string): void {
    this.selectedCategory.set(cat);
  }

  setEligibility(el: string): void {
    this.selectedEligibility.set(el);
  }

  resetAllFilters(): void {
    this.searchInputModel = '';
    this.searchQuery.set('');
    this.selectedCategory.set('All');
    this.selectedEligibility.set('All');
    this.selectedState.set('All');
    this.selectedMinistry.set('All');
  }

  hasActiveFilters(): boolean {
    return (
      this.searchQuery() !== '' ||
      this.selectedCategory() !== 'All' ||
      this.selectedEligibility() !== 'All' ||
      this.selectedState() !== 'All' ||
      this.selectedMinistry() !== 'All'
    );
  }

  toggleBookmark(item: PublicPolicyCard, event: Event): void {
    event.stopPropagation();
    const willBookmark = !item.bookmarked;

    // Optimistically update list
    this.policiesList.update(list =>
      list.map(p => p.id === item.id ? { ...p, bookmarked: willBookmark } : p)
    );

    // Update local storage
    const localSet = this.getLocalBookmarks();
    if (willBookmark) {
      localSet.add(String(item.id));
    } else {
      localSet.delete(String(item.id));
    }
    this.saveLocalBookmarks(localSet);

    // Sync with backend if authenticated
    const numId = typeof item.id === 'number' ? item.id : parseInt(String(item.id).replace(/\D/g, ''), 10);
    if (numId && !isNaN(numId) && this.auth.isAuthenticated()) {
      if (willBookmark) {
        this.dashboardService.savePolicy({ policy_id: numId }).subscribe({
          next: () => {},
          error: () => {}
        });
      } else {
        this.dashboardService.removeSavedPolicy(numId).subscribe({
          next: () => {},
          error: () => {}
        });
      }
    }
  }

  goToDetails(policyId: string | number): void {
    this.router.navigate(['/public/policies', policyId]);
  }

  readonly filteredPolicies = computed(() => {
    const q = this.searchQuery().toLowerCase();
    const cat = this.selectedCategory();
    const elig = this.selectedEligibility();
    const state = this.selectedState();
    const min = this.selectedMinistry();

    return this.policiesList().filter(policy => {
      const matchesQ = !q ||
        policy.title.toLowerCase().includes(q) ||
        policy.description.toLowerCase().includes(q) ||
        policy.category.toLowerCase().includes(q) ||
        policy.benefits.toLowerCase().includes(q) ||
        policy.eligibility.toLowerCase().includes(q);

      const matchesCat = cat === 'All' || policy.category.toLowerCase() === cat.toLowerCase();

      const matchesElig = elig === 'All' || 
        (policy.targetBeneficiary && policy.targetBeneficiary.toLowerCase().includes(elig.toLowerCase())) ||
        policy.eligibility.toLowerCase().includes(elig.toLowerCase());

      const matchesState = state === 'All' || (policy.state && (policy.state.toLowerCase() === state.toLowerCase() || policy.state === 'Central / All India'));

      const matchesMin = min === 'All' || (policy.ministry && policy.ministry.toLowerCase().includes(min.toLowerCase()));

      return matchesQ && matchesCat && matchesElig && matchesState && matchesMin;
    });
  });
}
