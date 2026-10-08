import { Component, OnInit, OnDestroy, inject, ChangeDetectorRef } from '@angular/core';
import { Router, ActivatedRoute, RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-verify-email',
  standalone: true,
  imports: [FormsModule, RouterLink],
  templateUrl: './verify-email.html',
  styleUrl: './verify-email.css',
})
export class VerifyEmail implements OnInit, OnDestroy {
  protected email = '';
  protected maskedEmail = '';
  protected otpDigits: string[] = ['', '', '', '', '', ''];
  protected isSubmitting = false;
  protected isResending = false;
  protected errorMessage = '';
  protected successMessage = '';

  // 5-minute (300s) OTP expiry timer
  protected expirySeconds = 300;
  protected expiryDisplay = '05:00';
  private expiryInterval: any = null;

  // 60-second Resend Cooldown
  protected resendCooldown = 60;
  protected canResend = false;
  private resendInterval: any = null;

  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);
  private readonly cdr = inject(ChangeDetectorRef);

  ngOnInit(): void {
    const rawEmail = this.route.snapshot.queryParams['email'] || '';
    this.email = rawEmail.trim();
    this.maskedEmail = this.maskEmail(this.email);

    if (!this.email) {
      this.errorMessage = 'No email address specified. Please register or sign in to verify your account.';
    }

    this.startExpiryTimer();
    this.startResendCooldown();
    this.cdr.detectChanges();
  }

  ngOnDestroy(): void {
    this.clearTimers();
  }

  private clearTimers(): void {
    if (this.expiryInterval) {
      clearInterval(this.expiryInterval);
      this.expiryInterval = null;
    }
    if (this.resendInterval) {
      clearInterval(this.resendInterval);
      this.resendInterval = null;
    }
  }

  private startExpiryTimer(): void {
    if (this.expiryInterval) clearInterval(this.expiryInterval);
    this.expirySeconds = 300;
    this.updateExpiryDisplay();

    this.expiryInterval = setInterval(() => {
      if (this.expirySeconds > 0) {
        this.expirySeconds--;
        this.updateExpiryDisplay();
      } else {
        clearInterval(this.expiryInterval);
        this.expiryInterval = null;
        this.errorMessage = 'Your verification code has expired. Please request a new code.';
      }
      this.cdr.detectChanges();
    }, 1000);
  }

  private updateExpiryDisplay(): void {
    const mins = Math.floor(this.expirySeconds / 60);
    const secs = this.expirySeconds % 60;
    this.expiryDisplay = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  }

  private startResendCooldown(): void {
    if (this.resendInterval) clearInterval(this.resendInterval);
    this.resendCooldown = 60;
    this.canResend = false;

    this.resendInterval = setInterval(() => {
      if (this.resendCooldown > 0) {
        this.resendCooldown--;
      } else {
        this.canResend = true;
        clearInterval(this.resendInterval);
        this.resendInterval = null;
      }
      this.cdr.detectChanges();
    }, 1000);
  }

  protected maskEmail(email: string): string {
    if (!email || !email.includes('@')) return email || 'your email';
    const [name, domain] = email.split('@');
    if (name.length <= 2) {
      return `${name}****@${domain}`;
    }
    const visibleStart = name.slice(0, 2);
    return `${visibleStart}****@${domain}`;
  }

  // OTP Input event handlers
  onDigitInput(event: Event, index: number): void {
    const input = event.target as HTMLInputElement;
    let value = input.value;

    // Handle single digit extraction
    if (value.length > 1) {
      value = value.slice(-1);
      input.value = value;
    }

    // Only allow numeric digits
    if (!/^\d*$/.test(value)) {
      input.value = '';
      this.otpDigits[index] = '';
      return;
    }

    this.otpDigits[index] = value;

    // Auto-advance to next input if filled
    if (value && index < 5) {
      const nextInput = document.getElementById(`otp-digit-${index + 1}`) as HTMLInputElement;
      if (nextInput) {
        nextInput.focus();
        nextInput.select();
      }
    }

    // Auto-submit if all 6 digits are filled
    if (this.isOtpComplete()) {
      this.onSubmit();
    }
  }

  onKeyDown(event: KeyboardEvent, index: number): void {
    const input = event.target as HTMLInputElement;

    if (event.key === 'Backspace') {
      if (!input.value && index > 0) {
        const prevInput = document.getElementById(`otp-digit-${index - 1}`) as HTMLInputElement;
        if (prevInput) {
          prevInput.focus();
          prevInput.select();
        }
      }
    } else if (event.key === 'ArrowLeft' && index > 0) {
      const prevInput = document.getElementById(`otp-digit-${index - 1}`) as HTMLInputElement;
      if (prevInput) prevInput.focus();
    } else if (event.key === 'ArrowRight' && index < 5) {
      const nextInput = document.getElementById(`otp-digit-${index + 1}`) as HTMLInputElement;
      if (nextInput) nextInput.focus();
    }
  }

  onPaste(event: ClipboardEvent): void {
    event.preventDefault();
    const pastedData = event.clipboardData?.getData('text') || '';
    const digitsOnly = pastedData.replace(/\D/g, '').slice(0, 6);

    if (!digitsOnly) return;

    for (let i = 0; i < 6; i++) {
      this.otpDigits[i] = digitsOnly[i] || '';
      const input = document.getElementById(`otp-digit-${i}`) as HTMLInputElement;
      if (input) {
        input.value = this.otpDigits[i];
      }
    }

    const focusIndex = Math.min(digitsOnly.length, 5);
    const targetInput = document.getElementById(`otp-digit-${focusIndex}`) as HTMLInputElement;
    if (targetInput) {
      targetInput.focus();
    }

    if (digitsOnly.length === 6) {
      this.onSubmit();
    }
  }

  isOtpComplete(): boolean {
    return this.otpDigits.every((d) => d !== '' && /^\d$/.test(d));
  }

  get otpCode(): string {
    return this.otpDigits.join('');
  }

  onSubmit(): void {
    this.errorMessage = '';
    this.successMessage = '';

    if (!this.email) {
      this.errorMessage = 'Please provide a valid email address.';
      this.cdr.detectChanges();
      return;
    }

    const code = this.otpCode;
    if (code.length !== 6 || !this.isOtpComplete()) {
      this.errorMessage = 'Please enter all 6 digits of your verification code.';
      this.cdr.detectChanges();
      return;
    }

    this.isSubmitting = true;
    this.cdr.detectChanges();

    this.authService.verifyOtp({ email: this.email, otp: code }).subscribe({
      next: (tokenResponse) => {
        this.isSubmitting = false;
        this.successMessage = 'Email verified successfully! Signing you in...';
        this.cdr.detectChanges();

        setTimeout(() => {
          const returnUrl = this.route.snapshot.queryParams['returnUrl'] || '/dashboard';
          this.router.navigateByUrl(returnUrl);
        }, 1000);
      },
      error: (err) => {
        this.isSubmitting = false;
        if (err.status === 400 || err.status === 422) {
          this.errorMessage = typeof err.error?.detail === 'string'
            ? err.error.detail
            : 'Invalid or expired verification code. Please check and try again.';
        } else if (err.status === 429) {
          this.errorMessage = err.error?.detail || 'Too many attempts. Please wait before trying again.';
        } else if (err.status === 0) {
          this.errorMessage = 'Unable to connect to the backend server. Please check your network connection.';
        } else {
          this.errorMessage = err.error?.detail || 'Verification failed. Please try again.';
        }
        this.cdr.detectChanges();
      }
    });
  }

  onResendOtp(): void {
    if (!this.canResend || this.isResending || !this.email) return;

    this.errorMessage = '';
    this.successMessage = '';
    this.isResending = true;
    this.cdr.detectChanges();

    this.authService.resendOtp({ email: this.email }).subscribe({
      next: (res) => {
        this.isResending = false;
        this.successMessage = res.message || 'A new verification code has been sent to your email.';
        // Reset inputs
        this.otpDigits = ['', '', '', '', '', ''];
        for (let i = 0; i < 6; i++) {
          const input = document.getElementById(`otp-digit-${i}`) as HTMLInputElement;
          if (input) input.value = '';
        }
        // Reset timers
        this.startExpiryTimer();
        this.startResendCooldown();
        // Focus first input
        const firstInput = document.getElementById('otp-digit-0') as HTMLInputElement;
        if (firstInput) firstInput.focus();
        this.cdr.detectChanges();
      },
      error: (err) => {
        this.isResending = false;
        if (err.status === 429) {
          this.errorMessage = err.error?.detail || 'Please wait before requesting another code.';
        } else {
          this.errorMessage = err.error?.detail || 'Failed to resend verification code. Please try again.';
        }
        this.cdr.detectChanges();
      }
    });
  }
}
