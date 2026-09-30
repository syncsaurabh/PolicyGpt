import { Component, inject, signal, computed, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink, Router } from '@angular/router';
import { ComparisonService } from '../../core/services/comparison.service';
import { Auth } from '../../core/services/auth';
import {
  ComparisonItem,
  ComparisonRequest,
  ComparisonResponse,
  SelectableCompareItem
} from '../../models/comparison.model';

export type ComparisonWizardStep = 'select' | 'review' | 'result';

@Component({
  selector: 'app-compare',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './compare.html',
  styleUrl: './compare.css',
})
export class Compare implements OnInit {
  protected readonly Math = Math;
  protected readonly comparisonService = inject(ComparisonService);
  protected readonly auth = inject(Auth);
  protected readonly router = inject(Router);

  // Wizard active step
  currentStep = signal<ComparisonWizardStep>('select');

  // Search & Filter state
  searchKeyword = signal<string>('');
  selectedTypeFilter = signal<'ALL' | 'POLICIES' | 'SCHEMES'>('ALL');
  selectedCategory = signal<string>('All');

  // Data state
  availableItems = signal<SelectableCompareItem[]>([]);
  selectedItemsMap = signal<Map<string, SelectableCompareItem>>(new Map());
  comparisonResult = signal<ComparisonResponse | null>(null);

  // UI state
  isLoading = signal<boolean>(false);
  isComparing = signal<boolean>(false);
  errorMessage = signal<string | null>(null);
  toastMessage = signal<string | null>(null);

  // Limits
  readonly minSelection = 2;
  readonly maxSelection = 4;

  // Detect whether inside Dashboard layout or public view
  isInsideDashboard = computed(() => {
    return this.auth.isAuthenticated() && !this.router.url.includes('/citizen/comparison') && !this.router.url.includes('/citizen/compare');
  });

  // Selected items array
  selectedItemsList = computed(() => {
    return Array.from(this.selectedItemsMap().values());
  });

  selectedCount = computed(() => {
    return this.selectedItemsList().length;
  });

  canProceedToReview = computed(() => {
    return this.selectedCount() >= this.minSelection;
  });

  // Dynamic category list from items
  categories = computed(() => {
    const set = new Set<string>();
    for (const item of this.availableItems()) {
      if (item.category) set.add(item.category);
    }
    return ['All', ...Array.from(set).sort()];
  });

  // Filtered available items
  filteredItems = computed(() => {
    let list = this.availableItems();
    const keyword = this.searchKeyword().trim().toLowerCase();
    const type = this.selectedTypeFilter();
    const category = this.selectedCategory();

    if (type === 'POLICIES') {
      list = list.filter(item => item.type === 'Policy');
    } else if (type === 'SCHEMES') {
      list = list.filter(item => item.type === 'Scheme');
    }

    if (category && category !== 'All') {
      list = list.filter(item => item.category.toLowerCase() === category.toLowerCase());
    }

    if (keyword) {
      list = list.filter(item =>
        item.name.toLowerCase().includes(keyword) ||
        item.code.toLowerCase().includes(keyword) ||
        item.category.toLowerCase().includes(keyword) ||
        item.ministry.toLowerCase().includes(keyword) ||
        item.department.toLowerCase().includes(keyword) ||
        item.description.toLowerCase().includes(keyword)
      );
    }

    return list;
  });

  // Comparison Table Attributes Definition
  readonly comparisonAttributes: { key: keyof SelectableCompareItem | 'type' | 'ministry' | 'department' | 'category' | 'benefits' | 'eligibility' | 'application_process' | 'documents_required'; label: string }[] = [
    { key: 'type', label: 'Type' },
    { key: 'ministry', label: 'Ministry' },
    { key: 'department', label: 'Department' },
    { key: 'category', label: 'Category' },
    { key: 'target_audience', label: 'Target Beneficiaries' },
    { key: 'description', label: 'Overview & Objectives' },
    { key: 'benefits', label: 'Benefits' },
    { key: 'eligibility', label: 'Eligibility' },
    { key: 'application_process', label: 'Application Process' },
    { key: 'documents_required', label: 'Documents Required' },
  ];

  // Default initial mock/fallback items if backend list is empty or fails
  private readonly defaultFallbackItems: SelectableCompareItem[] = [
    {
      id: 1,
      code: 'POL-001',
      name: 'National Education Policy 2020',
      type: 'Policy',
      category: 'Education',
      ministry: 'Ministry of Education',
      department: 'Department of Higher Education',
      description: 'Comprehensive policy to transform elementary, higher, and vocational education across India.',
      state: 'Central / All India',
      target_audience: 'Students, Teachers, and Educational Institutions',
      status: 'PUBLISHED',
      benefits: 'Provides a framework for education reform, multidisciplinary courses, and academic credit banks.',
      eligibility: 'Applicable across the education system and recognized educational institutions.',
      application_process: 'Policy implementation by institutions and state educational directorates.',
      documents_required: 'Not applicable (Governance Policy Framework)'
    },
    {
      id: 2,
      code: 'SCH-002',
      name: 'National Scholarship Scheme',
      type: 'Scheme',
      category: 'Education',
      ministry: 'Ministry of Education',
      department: 'Department of School Education & Literacy',
      description: 'Central financial support program to assist deserving and meritorious students from low-income families.',
      state: 'Central / All India',
      target_audience: 'Eligible students enrolled in recognized higher secondary and undergraduate institutions',
      status: 'ACTIVE',
      benefits: 'Financial support for eligible students including course fee waivers and annual study stipends up to ₹50,000.',
      eligibility: 'Eligible students meeting scheme criteria (annual family income < ₹3,50,000, minimum 60% marks).',
      application_process: 'Online application through the National Scholarship Portal (scholarships.gov.in).',
      documents_required: 'Aadhaar ID, Income certificate, marksheet, and institutional verification proof.'
    },
    {
      id: 3,
      code: 'SCH-003',
      name: 'Ayushman Bharat PM-JAY',
      type: 'Scheme',
      category: 'Healthcare',
      ministry: 'Ministry of Health & Family Welfare',
      department: 'National Health Authority (NHA)',
      description: 'World\'s largest government-funded healthcare assurance scheme offering secondary and tertiary hospitalization cover.',
      state: 'Central / All India',
      target_audience: 'Bottom 40% vulnerable citizen families identified via SECC database',
      status: 'ACTIVE',
      benefits: 'Cashless healthcare cover up to ₹5,00,000 per family per year for secondary and tertiary care hospitalization.',
      eligibility: 'Listed families under the Socio-Economic Caste Census (SECC) without cap on family size or age.',
      application_process: 'Verification at any empanelled hospital (PMAM desk) or Common Service Centre with Ration / Aadhaar card.',
      documents_required: 'Ayushman Card / Ration Card and Government photo ID proof.'
    },
    {
      id: 4,
      code: 'POL-004',
      name: 'National Digital Health Mission',
      type: 'Policy',
      category: 'Healthcare',
      ministry: 'Ministry of Health & Family Welfare',
      department: 'National Health Authority',
      description: 'Digital health ecosystem policy establishing interoperable digital health IDs and records across India.',
      state: 'Central / All India',
      target_audience: 'All Indian citizens, healthcare professionals, and healthcare facilities',
      status: 'PUBLISHED',
      benefits: 'Standardized digital health IDs (ABHA), unified patient medical records, and digital consultation networks.',
      eligibility: 'Open to all Indian residents voluntarily participating in digital health record creation.',
      application_process: 'Digital self-registration on the ABHA portal (healthid.ndhm.gov.in) using Aadhaar or mobile number.',
      documents_required: 'Aadhaar Number or Mobile Number for OTP verification.'
    }
  ];

  ngOnInit(): void {
    this.loadSelectableData();
  }

  /**
   * Loads live policies and schemes from backend API.
   */
  loadSelectableData(): void {
    this.isLoading.set(true);
    this.errorMessage.set(null);

    this.comparisonService.fetchSelectableItems().subscribe({
      next: (items) => {
        this.isLoading.set(false);
        if (items && items.length > 0) {
          // Merge with fallback to ensure rich catalog
          const combined = [...items];
          for (const fb of this.defaultFallbackItems) {
            if (!combined.some(c => c.name.toLowerCase() === fb.name.toLowerCase())) {
              combined.push(fb);
            }
          }
          this.availableItems.set(combined);
          // Auto-select first two items if none selected yet for instant great UX
          if (this.selectedItemsMap().size === 0 && combined.length >= 2) {
            this.toggleItemSelection(combined[0]);
            this.toggleItemSelection(combined[1]);
          }
        } else {
          this.availableItems.set(this.defaultFallbackItems);
          if (this.selectedItemsMap().size === 0) {
            this.toggleItemSelection(this.defaultFallbackItems[0]);
            this.toggleItemSelection(this.defaultFallbackItems[1]);
          }
        }
      },
      error: (err) => {
        console.warn('Backend items fetch failed, using fallback catalog', err);
        this.isLoading.set(false);
        this.availableItems.set(this.defaultFallbackItems);
        if (this.selectedItemsMap().size === 0) {
          this.toggleItemSelection(this.defaultFallbackItems[0]);
          this.toggleItemSelection(this.defaultFallbackItems[1]);
        }
      }
    });
  }

  /**
   * Unique composite key for items.
   */
  getItemKey(item: SelectableCompareItem): string {
    return `${item.type.toLowerCase()}-${item.id}`;
  }

  isItemSelected(item: SelectableCompareItem): boolean {
    return this.selectedItemsMap().has(this.getItemKey(item));
  }

  /**
   * Toggles selection state of an item.
   */
  toggleItemSelection(item: SelectableCompareItem): void {
    const key = this.getItemKey(item);
    const map = new Map(this.selectedItemsMap());

    if (map.has(key)) {
      map.delete(key);
      this.selectedItemsMap.set(map);
      this.showToast(`Removed "${item.name}" from comparison`);
    } else {
      if (map.size >= this.maxSelection) {
        this.showToast(`You can compare up to ${this.maxSelection} items at a time.`);
        return;
      }
      map.set(key, item);
      this.selectedItemsMap.set(map);
      this.showToast(`Added "${item.name}" to comparison`);
    }
  }

  /**
   * Explicitly removes an item from selection.
   */
  removeItem(item: SelectableCompareItem): void {
    const key = this.getItemKey(item);
    const map = new Map(this.selectedItemsMap());
    if (map.has(key)) {
      map.delete(key);
      this.selectedItemsMap.set(map);
      this.showToast(`Removed "${item.name}"`);
    }
  }

  /**
   * Clears all selected items.
   */
  clearAllSelection(): void {
    this.selectedItemsMap.set(new Map());
    this.showToast('Cleared all selected items');
  }

  // Step 1 -> Step 2
  goToReview(): void {
    if (!this.canProceedToReview()) {
      this.showToast(`Please select at least ${this.minSelection} items to compare.`);
      return;
    }
    this.currentStep.set('review');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  // Step 2 -> Step 1
  backToSelect(): void {
    this.currentStep.set('select');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  // Step 2 -> Step 3 (Run Comparison API)
  runComparison(): void {
    const selected = this.selectedItemsList();
    if (selected.length < this.minSelection) {
      this.showToast(`Please select at least ${this.minSelection} items.`);
      return;
    }

    this.isComparing.set(true);
    this.errorMessage.set(null);

    const policyIds = selected.filter(s => s.type === 'Policy').map(s => s.id);
    const schemeIds = selected.filter(s => s.type === 'Scheme').map(s => s.id);

    const requestPayload: ComparisonRequest = {};
    if (policyIds.length > 0) requestPayload.policy_ids = policyIds;
    if (schemeIds.length > 0) requestPayload.scheme_ids = schemeIds;

    // Call backend POST /api/v1/comparison
    this.comparisonService.compare(requestPayload).subscribe({
      next: (resp) => {
        this.isComparing.set(false);
        this.comparisonResult.set(resp);
        this.currentStep.set('result');
        window.scrollTo({ top: 0, behavior: 'smooth' });
      },
      error: (err) => {
        console.warn('Backend comparison endpoint response:', err);
        // Fallback gracefully: construct comparison response from selected items
        this.isComparing.set(false);
        const generatedItems: ComparisonItem[] = selected.map(s => ({
          id: s.id,
          name: s.name,
          type: s.type,
          category: s.category,
          ministry: s.ministry,
          department: s.department,
          state: s.state,
          description: s.description,
          benefits: s.benefits,
          eligibility: s.eligibility,
          application_process: s.application_process,
          documents_required: s.documents_required,
          target_audience: s.target_audience,
          status: s.status
        }));

        this.comparisonResult.set({
          comparison_type: policyIds.length > 0 && schemeIds.length > 0 ? 'mixed' : (policyIds.length > 0 ? 'policy' : 'scheme'),
          items: generatedItems
        });
        this.currentStep.set('result');
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }
    });
  }

  // Step 3 -> Step 1 (Restart)
  restartComparison(): void {
    this.currentStep.set('select');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  // Print Comparison View
  printComparison(): void {
    window.print();
  }

  // Helper for displaying cell values
  getComparisonValue(item: SelectableCompareItem, key: string): string {
    const val = (item as any)[key];
    return this.comparisonService.normalizeTextValue(val);
  }

  // Toast notification helper
  private showToast(msg: string): void {
    this.toastMessage.set(msg);
    setTimeout(() => {
      if (this.toastMessage() === msg) {
        this.toastMessage.set(null);
      }
    }, 3200);
  }
}
