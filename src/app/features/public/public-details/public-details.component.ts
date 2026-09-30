import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { CitizenHeaderComponent } from '../citizen-dashboard/components/citizen-header/citizen-header.component';
import { CitizenFooterComponent } from '../citizen-dashboard/components/citizen-footer/citizen-footer.component';
import { PolicyService } from '../../../core/services/policy.service';
import { SchemeService } from '../../../core/services/scheme.service';
import { DashboardService } from '../../../core/services/dashboard.service';
import { Auth } from '../../../core/services/auth';

export interface PublicDetailModel {
  id: string | number;
  title: string;
  fullName: string;
  category: string;
  description: string;
  aboutText: string;
  benefits: string[];
  eligibility: string;
  beneficiary: string;
  status: string;
  officialUrl?: string;
  whoCanApply: string[];
  requiredInfo: string[];
  steps: { stepNumber: string; title: string; desc: string }[];
  isBookmarked?: boolean;
}

@Component({
  selector: 'app-public-details',
  standalone: true,
  imports: [CommonModule, RouterLink, CitizenHeaderComponent, CitizenFooterComponent],
  templateUrl: './public-details.component.html',
  styleUrl: './public-details.component.css'
})
export class PublicDetailsComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly policyService = inject(PolicyService);
  private readonly schemeService = inject(SchemeService);
  private readonly dashboardService = inject(DashboardService);
  private readonly auth = inject(Auth);

  isLoading = signal<boolean>(false);
  itemType = signal<'policy' | 'scheme'>('policy');
  detail = signal<PublicDetailModel | null>(null);

  // Pre-configured rich templates for known schemes/policies matching design
  private readonly presetDetails: Record<string, PublicDetailModel> = {
    'pm-kisan': {
      id: 'pm-kisan',
      title: 'PM-KISAN',
      fullName: 'Pradhan Mantri Kisan Samman Nidhi',
      category: 'Agriculture',
      description: 'Income support for eligible farmer families to help meet agricultural and household needs.',
      aboutText: 'PM-KISAN provides income support to eligible farmer families to help meet agricultural and household needs.',
      benefits: [
        'Financial assistance of ₹6,000 per year in three equal 4-monthly installments',
        'Direct benefit transfer (DBT) into verified bank accounts',
        'Comprehensive support for agricultural and household crop expenses'
      ],
      eligibility: 'Eligible farmers',
      beneficiary: 'Farmer families',
      status: 'Active',
      officialUrl: 'https://pmkisan.gov.in',
      whoCanApply: [
        'Eligible farmer families with cultivable landholding',
        "Meets the scheme's eligibility criteria and statutory guidelines",
        'Required beneficiary Aadhaar and land records available'
      ],
      requiredInfo: [
        'Identity information (Aadhaar Card)',
        'Active bank account details (IFSC & Account No)',
        'Land / farmer ownership records'
      ],
      steps: [
        {
          stepNumber: '01',
          title: 'Check Eligibility',
          desc: "Confirm that you meet the scheme's eligibility requirements"
        },
        {
          stepNumber: '02',
          title: 'Prepare Information',
          desc: 'Keep the required information and documents ready'
        },
        {
          stepNumber: '03',
          title: 'Apply Online',
          desc: 'Visit the official application portal and submit your application'
        }
      ],
      isBookmarked: false
    },
    'ayushman-bharat': {
      id: 'ayushman-bharat',
      title: 'Ayushman Bharat',
      fullName: 'Pradhan Mantri Jan Arogya Yojana (PM-JAY)',
      category: 'Healthcare',
      description: 'Universal health coverage and cashless hospitalization protection for vulnerable families.',
      aboutText: 'Ayushman Bharat PM-JAY is the world’s largest government-funded healthcare assurance initiative providing secondary and tertiary care hospitalization.',
      benefits: [
        'Cashless coverage up to ₹5,00,000 per family per year',
        'Valid at all empanelled public and private hospitals across India',
        'Pre-existing conditions covered from day one of enrollment'
      ],
      eligibility: 'Eligible families',
      beneficiary: 'Low-income households',
      status: 'Active',
      officialUrl: 'https://pmjay.gov.in',
      whoCanApply: [
        'Families listed in the Socio-Economic Caste Census (SECC) database',
        'Holders of valid NFSA Ration cards or state beneficiary registers',
        'Senior citizens in designated income categories'
      ],
      requiredInfo: [
        'Aadhaar Card or national identity proof',
        'Ration Card / PM-JAY Family ID card',
        'Registered mobile number for OTP verification'
      ],
      steps: [
        {
          stepNumber: '01',
          title: 'Check Eligibility',
          desc: 'Verify your name in the Ayushman beneficiary database online or at CSC'
        },
        {
          stepNumber: '02',
          title: 'Generate Golden Card',
          desc: 'Complete e-KYC verification at any empanelled hospital or kiosk'
        },
        {
          stepNumber: '03',
          title: 'Avail Cashless Care',
          desc: 'Present your Ayushman Card for 100% cashless medical treatments'
        }
      ],
      isBookmarked: false
    },
    'national-scholarship-portal': {
      id: 'national-scholarship-portal',
      title: 'National Scholarship Portal',
      fullName: 'National Scholarship Portal & Central Sector Schemes',
      category: 'Education',
      description: 'Unified online portal offering direct financial scholarship assistance to eligible students across India.',
      aboutText: 'The National Scholarship Portal (NSP) provides a common electronic window for students to apply for central, UGC, AICTE and state-level educational grants.',
      benefits: [
        'Tuition fee reimbursement and monthly stipend allowances',
        'Direct Benefit Transfer directly to student bank accounts',
        'Covers pre-matric, post-matric, and higher professional education'
      ],
      eligibility: 'Eligible students',
      beneficiary: 'School & college students',
      status: 'Active',
      officialUrl: 'https://scholarships.gov.in',
      whoCanApply: [
        'Students enrolled in recognized schools, colleges, or universities',
        'Applicants meeting family annual income thresholds (as specified per scheme)',
        'Academic merit criteria satisfied in the qualifying examination'
      ],
      requiredInfo: [
        'Student Aadhaar and active bank account in student name',
        'Previous academic marksheets and admission proof',
        'Income certificate and caste/category certificate (if applicable)'
      ],
      steps: [
        {
          stepNumber: '01',
          title: 'Check Eligibility',
          desc: 'Browse NSP scholarship schemes that match your study level'
        },
        {
          stepNumber: '02',
          title: 'Prepare Information',
          desc: 'Gather academic mark sheets, income proofs, and bank details'
        },
        {
          stepNumber: '03',
          title: 'Apply Online',
          desc: 'Register OTR (One Time Registration) and submit NSP application'
        }
      ],
      isBookmarked: false
    }
  };

  ngOnInit(): void {
    this.route.paramMap.subscribe(params => {
      const id = params.get('id') || 'pm-kisan';
      const path = this.route.snapshot.routeConfig?.path || '';
      if (path.includes('schemes') || this.route.snapshot.url.some(u => u.path === 'schemes')) {
        this.itemType.set('scheme');
      } else {
        this.itemType.set('policy');
      }
      this.loadItemDetail(id);
    });
  }

  loadItemDetail(id: string): void {
    const normalizedKey = id.toLowerCase().trim();
    if (this.presetDetails[normalizedKey]) {
      this.detail.set(this.presetDetails[normalizedKey]);
      return;
    }

    // Attempt live API fetch from backend
    this.isLoading.set(true);
    if (this.itemType() === 'scheme') {
      this.schemeService.getScheme(id).subscribe({
        next: (res) => {
          this.isLoading.set(false);
          this.detail.set(this.mapSchemeToDetail(res));
        },
        error: () => {
          this.isLoading.set(false);
          this.detail.set(this.getGenericFallback(id, 'scheme'));
        }
      });
    } else {
      this.policyService.getPolicy(id).subscribe({
        next: (res) => {
          this.isLoading.set(false);
          this.detail.set(this.mapPolicyToDetail(res));
        },
        error: () => {
          this.isLoading.set(false);
          this.detail.set(this.getGenericFallback(id, 'policy'));
        }
      });
    }
  }

  private mapPolicyToDetail(dto: any): PublicDetailModel {
    return {
      id: dto.id,
      title: dto.title || dto.policy_name || 'Government Policy',
      fullName: dto.policy_name || dto.title || 'Official Government Policy Initiative',
      category: dto.category || 'General',
      description: dto.description || 'Comprehensive government policy initiative supporting national welfare and civic development.',
      aboutText: dto.description || 'This policy establishes structured legal frameworks, administrative guidelines, and public benefits.',
      benefits: dto.benefits_summary ? [dto.benefits_summary] : [
        'Statutory protections and administrative support',
        'Standardized public access and governance transparency',
        'Structured welfare assistance for target beneficiaries'
      ],
      eligibility: dto.eligibility_summary || 'Eligible citizens',
      beneficiary: dto.target_beneficiary || 'Citizen families',
      status: dto.status || 'Active',
      officialUrl: 'https://india.gov.in',
      whoCanApply: [
        'Eligible citizens and designated beneficiary groups',
        "Meets the policy's criteria and regulatory framework",
        'Required identification documents available'
      ],
      requiredInfo: [
        'Identity proof (Aadhaar / Voter ID)',
        'Proof of residence or registration documents',
        'Supporting beneficiary verification forms'
      ],
      steps: [
        { stepNumber: '01', title: 'Check Eligibility', desc: "Confirm that you meet the policy's eligibility criteria" },
        { stepNumber: '02', title: 'Prepare Information', desc: 'Keep the required documents and verification records ready' },
        { stepNumber: '03', title: 'Apply Online', desc: 'Visit the official government portal to submit your application' }
      ],
      isBookmarked: false
    };
  }

  private mapSchemeToDetail(dto: any): PublicDetailModel {
    return {
      id: dto.id,
      title: dto.scheme_name || dto.name || 'Government Scheme',
      fullName: dto.name || dto.scheme_name || 'Official Welfare Scheme',
      category: dto.category || 'General',
      description: dto.description || dto.tagline || 'Government welfare initiative providing benefits to citizens.',
      aboutText: dto.description || 'This scheme provides targeted welfare assistance and direct citizen benefits.',
      benefits: dto.benefits_summary ? [dto.benefits_summary] : [
        dto.benefits || 'Financial assistance and welfare grant',
        'Direct Benefit Transfer (DBT) to beneficiary account',
        'End-to-end transparent grievance redressal'
      ],
      eligibility: dto.eligibility_summary || 'Eligible applicants',
      beneficiary: dto.target_beneficiary || 'Eligible families',
      status: dto.status || 'Active',
      officialUrl: 'https://india.gov.in',
      whoCanApply: [
        'Eligible citizen beneficiaries in the specified category',
        "Meets all scheme rules and socio-economic criteria",
        'Valid documentation and banking records ready'
      ],
      requiredInfo: [
        'Government-issued Photo Identity Proof',
        'Bank Account Details (IFSC Code & Account Number)',
        'Category or Income Certificate where required'
      ],
      steps: [
        { stepNumber: '01', title: 'Check Eligibility', desc: "Confirm that you meet the scheme's criteria" },
        { stepNumber: '02', title: 'Prepare Information', desc: 'Gather all required identity, income, and bank records' },
        { stepNumber: '03', title: 'Apply Online', desc: 'Submit your application through the official scheme portal' }
      ],
      isBookmarked: false
    };
  }

  private getGenericFallback(id: string, type: 'policy' | 'scheme'): PublicDetailModel {
    return {
      id,
      title: id.toUpperCase().replace(/-/g, ' '),
      fullName: `Government ${type === 'policy' ? 'Policy' : 'Scheme'} Initiative`,
      category: 'General',
      description: 'Government initiative designed to deliver public welfare benefits and institutional support to citizens.',
      aboutText: 'Detailed information and guidelines for citizens regarding application procedures, eligibility, and service delivery.',
      benefits: [
        'Direct citizen financial or institutional support',
        'Transparent digital application and tracking',
        'Timely grievance redressal and updates'
      ],
      eligibility: 'Eligible citizens',
      beneficiary: 'Designated groups',
      status: 'Active',
      officialUrl: 'https://india.gov.in',
      whoCanApply: [
        'Eligible citizens satisfying primary criteria',
        'Applicants meeting all regulatory requirements',
        'Proper documentation available'
      ],
      requiredInfo: [
        'Identity proof (Aadhaar / National ID)',
        'Bank account details for DBT transfer',
        'Address and demographic proof'
      ],
      steps: [
        { stepNumber: '01', title: 'Check Eligibility', desc: 'Verify your eligibility criteria on the portal' },
        { stepNumber: '02', title: 'Prepare Information', desc: 'Keep required information and papers ready' },
        { stepNumber: '03', title: 'Apply Online', desc: 'Visit the official website and complete your submission' }
      ],
      isBookmarked: false
    };
  }

  toggleSaveScheme(): void {
    const current = this.detail();
    if (!current) return;

    const willBookmark = !current.isBookmarked;
    this.detail.update(d => d ? { ...d, isBookmarked: willBookmark } : null);

    const storageKey = this.itemType() === 'scheme' ? 'scheme_bookmarks' : 'policy_bookmarks';
    try {
      const stored = localStorage.getItem(storageKey);
      const set = stored ? new Set(JSON.parse(stored)) : new Set();
      if (willBookmark) {
        set.add(String(current.id));
      } else {
        set.delete(String(current.id));
      }
      localStorage.setItem(storageKey, JSON.stringify(Array.from(set)));
    } catch {}

    const numId = typeof current.id === 'number' ? current.id : parseInt(String(current.id).replace(/\D/g, ''), 10);
    if (numId && !isNaN(numId) && this.auth.isAuthenticated()) {
      if (willBookmark) {
        const payload = this.itemType() === 'scheme' ? { scheme_id: numId } : { policy_id: numId };
        this.dashboardService.savePolicy(payload).subscribe({
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

  openOfficialPortal(): void {
    const url = this.detail()?.officialUrl || 'https://india.gov.in';
    window.open(url, '_blank');
  }
}
