import { Component, inject, signal, computed, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { CitizenHeaderComponent } from '../citizen-dashboard/components/citizen-header/citizen-header.component';
import { CitizenFooterComponent } from '../citizen-dashboard/components/citizen-footer/citizen-footer.component';
import { SchemeService } from '../../../core/services/scheme.service';
import { DashboardService } from '../../../core/services/dashboard.service';
import { Auth } from '../../../core/services/auth';
import { SchemeReadDto } from '../../../models/scheme.model';

export interface PublicSchemeCard {
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
  selector: 'app-public-schemes',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, CitizenHeaderComponent, CitizenFooterComponent],
  templateUrl: './public-schemes.component.html',
  styleUrl: './public-schemes.component.css'
})
export class PublicSchemesComponent implements OnInit {
  private readonly schemeService = inject(SchemeService);
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
  schemesList = signal<PublicSchemeCard[]>([]);

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

  // Default initial featured schemes matching design
  private readonly fallbackSchemes: PublicSchemeCard[] = [
    {
      id: 'pm-kisan',
      title: 'PM-KISAN',
      category: 'Agriculture',
      description: 'Financial support for eligible farmers to support their agricultural needs',
      eligibility: 'Eligible farmers',
      benefits: 'Financial assistance of ₹6,000 annually',
      state: 'Central / All India',
      ministry: 'Ministry of Agriculture & Farmers Welfare',
      targetBeneficiary: 'Farmers',
      bookmarked: false
    },
    {
      id: 'ayushman-bharat',
      title: 'Ayushman Bharat',
      category: 'Healthcare',
      description: 'Healthcare support and financial protection for eligible families',
      eligibility: 'Eligible families',
      benefits: 'Healthcare coverage up to ₹5 Lakh',
      state: 'Central / All India',
      ministry: 'Ministry of Health and Family Welfare',
      targetBeneficiary: 'Families',
      bookmarked: false
    },
    {
      id: 'national-scholarship-portal',
      title: 'National Scholarship Portal',
      category: 'Education',
      description: 'A platform to access and apply for scholarships for eligible students',
      eligibility: 'Eligible students',
      benefits: 'Scholarship assistance & fee support',
      state: 'Central / All India',
      ministry: 'Ministry of Education',
      targetBeneficiary: 'Students',
      bookmarked: false
    },
    {
      id: 'pm-awas-yojana',
      title: 'Pradhan Mantri Awas Yojana (PMAY)',
      category: 'Housing',
      description: 'Credit-linked subsidy and housing assistance for urban & rural families',
      eligibility: 'Eligible families without pucca house',
      benefits: 'Interest subsidy on home loans up to ₹2.67 Lakh',
      state: 'Central / All India',
      ministry: 'Ministry of Housing and Urban Affairs',
      targetBeneficiary: 'Families',
      bookmarked: false
    },
    {
      id: 'pm-mudra-yojana',
      title: 'Pradhan Mantri Mudra Yojana (PMMY)',
      category: 'Employment',
      description: 'Collateral-free institutional loans for micro & small enterprises',
      eligibility: 'Micro-entrepreneurs and business owners',
      benefits: 'Loans up to ₹10 Lakh with subsidized interest',
      state: 'Central / All India',
      ministry: 'Ministry of Finance',
      targetBeneficiary: 'Students',
      bookmarked: false
    },
    {
      id: 'sukanya-samriddhi',
      title: 'Sukanya Samriddhi Yojana (SSY)',
      category: 'Women',
      description: 'Government savings scheme securing education & future of girl child',
      eligibility: 'Parents of girl child below 10 years',
      benefits: 'Guaranteed 8.2% tax-free interest growth',
      state: 'Central / All India',
      ministry: 'Ministry of Women & Child Development',
      targetBeneficiary: 'Families',
      bookmarked: false
    }
  ];

  ngOnInit(): void {
    this.fetchSchemes();
  }

  fetchSchemes(): void {
    this.isLoading.set(true);
    const localBookmarks = this.getLocalBookmarks();

    this.schemeService.listSchemes().subscribe({
      next: (res) => {
        this.isLoading.set(false);
        const results = res?.results;
        if (results && results.length > 0) {
          const mapped: PublicSchemeCard[] = results.map((dto: SchemeReadDto) => ({
            id: dto.id,
            title: dto.name || 'Government Scheme',
            category: dto.category || 'General',
            description: dto.description || dto.benefits || 'Explore official welfare initiative and public citizen benefits.',
            eligibility: dto.target_audience || 'Eligible citizen beneficiaries',
            benefits: dto.benefits || 'Structured welfare support and direct assistance',
            state: dto.state || 'Central / All India',
            ministry: dto.ministry || dto.department || 'Government of India',
            targetBeneficiary: dto.target_audience || 'Families',
            bookmarked: localBookmarks.has(String(dto.id))
          }));

          const combined = [...mapped];
          for (const fb of this.fallbackSchemes) {
            if (!combined.some(c => String(c.id).toLowerCase() === String(fb.id).toLowerCase() || c.title.toLowerCase() === fb.title.toLowerCase())) {
              combined.push({
                ...fb,
                bookmarked: localBookmarks.has(String(fb.id))
              });
            }
          }
          this.schemesList.set(combined);
        } else {
          this.schemesList.set(this.fallbackSchemes.map(fb => ({
            ...fb,
            bookmarked: localBookmarks.has(String(fb.id))
          })));
        }

        // Sync with backend if user is authenticated
        if (this.auth.isAuthenticated()) {
          this.syncBackendBookmarks();
        }
      },
      error: () => {
        this.isLoading.set(false);
        this.schemesList.set(this.fallbackSchemes.map(fb => ({
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
      const stored = localStorage.getItem('scheme_bookmarks');
      return stored ? new Set(JSON.parse(stored)) : new Set();
    } catch {
      return new Set();
    }
  }

  private saveLocalBookmarks(bookmarks: Set<string>): void {
    try {
      localStorage.setItem('scheme_bookmarks', JSON.stringify(Array.from(bookmarks)));
    } catch {}
  }

  private syncBackendBookmarks(): void {
    this.dashboardService.getCitizenDashboard().subscribe({
      next: (dash) => {
        if (dash.saved_policies) {
          const backendIds = new Set<string>();
          dash.saved_policies.forEach(sp => {
            if (sp.scheme_id) backendIds.add(String(sp.scheme_id));
            if (sp.item_type === 'scheme' && sp.id) backendIds.add(String(sp.id));
          });
          const localSet = this.getLocalBookmarks();
          backendIds.forEach(id => localSet.add(id));
          this.saveLocalBookmarks(localSet);

          this.schemesList.update(list =>
            list.map(s => ({
              ...s,
              bookmarked: backendIds.has(String(s.id)) || localSet.has(String(s.id))
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

  toggleBookmark(scheme: PublicSchemeCard, event: Event): void {
    event.stopPropagation();
    const willBookmark = !scheme.bookmarked;

    // Optimistically update list
    this.schemesList.update(list =>
      list.map(s => s.id === scheme.id ? { ...s, bookmarked: willBookmark } : s)
    );

    // Update local storage
    const localSet = this.getLocalBookmarks();
    if (willBookmark) {
      localSet.add(String(scheme.id));
    } else {
      localSet.delete(String(scheme.id));
    }
    this.saveLocalBookmarks(localSet);

    // Sync with backend if authenticated
    const numId = typeof scheme.id === 'number' ? scheme.id : parseInt(String(scheme.id).replace(/\D/g, ''), 10);
    if (numId && !isNaN(numId) && this.auth.isAuthenticated()) {
      if (willBookmark) {
        this.dashboardService.savePolicy({ scheme_id: numId }).subscribe({
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

  goToDetails(schemeId: string | number): void {
    this.router.navigate(['/public/schemes', schemeId]);
  }

  readonly filteredSchemes = computed(() => {
    const q = this.searchQuery().toLowerCase().trim();
    const cat = this.selectedCategory();
    const elig = this.selectedEligibility();
    const state = this.selectedState();
    const min = this.selectedMinistry();

    return this.schemesList().filter(scheme => {
      const matchesQ = !q ||
        scheme.title.toLowerCase().includes(q) ||
        scheme.description.toLowerCase().includes(q) ||
        scheme.category.toLowerCase().includes(q) ||
        (scheme.benefits && scheme.benefits.toLowerCase().includes(q)) ||
        (scheme.eligibility && scheme.eligibility.toLowerCase().includes(q));

      const matchesCat = cat === 'All' || scheme.category.toLowerCase() === cat.toLowerCase();

      const matchesElig = elig === 'All' || 
        (scheme.targetBeneficiary && scheme.targetBeneficiary.toLowerCase().includes(elig.toLowerCase())) ||
        (scheme.eligibility && scheme.eligibility.toLowerCase().includes(elig.toLowerCase()));

      const matchesState = state === 'All' || (scheme.state && (scheme.state.toLowerCase() === state.toLowerCase() || scheme.state === 'Central / All India'));

      const matchesMin = min === 'All' || (scheme.ministry && scheme.ministry.toLowerCase().includes(min.toLowerCase()));

      return matchesQ && matchesCat && matchesElig && matchesState && matchesMin;
    });
  });
}
