# 🔐 Zango Auth Upgrade Specification

  

## 📊 Configuration Hierarchy

  

3-tier system with this priority:

**User Level > Role Level > Tenant Level**

  

- 🏢 **Tenant Level**: Sets baseline policies (password rules, login methods, 2FA defaults)

- 👥 **Role Level**: Can override tenant settings (e.g., admin roles need stronger security)

- 👤 **User Level**: Personal preferences that can only be MORE restrictive (if 2FA, SSO Enforced at user role level then can't be disabled at user level)

  

## 🎯 Key Features

### Authentication Methods

- Password-based login (can be disabled per role)

- SSO (SAML)

- OIDC (Google, Microsoft, etc.)


### 2FA Methods (using django-otp package)

-  **TOTP**: Authenticator apps (Google Authenticator, Authy)

-  **SMS OTP**: 6-digit codes via SMS

-  **Email OTP**: 6-digit codes via email

-  **Backup Codes**: 8 one-time recovery codes for TOTP

  

## 🔄 Authentication Flow

  

1.  **Login**: User authenticates via Password/SSO/OIDC

2.  **Role Selection**: Choose role (if multiple available)

3.  **Configuration Applied**: System uses effective config for selected role

4.  **2FA Check**: If required but not setup → Setup flow, If setup → Verification

5.  **Access Granted**: Session created with appropriate policies

  

## 🔐 2FA Setup Process Flow

  

### First-Time 2FA Setup

1.  **Method Selection**

- System checks allowed 2FA methods for user's role

- User selects from available options (TOTP/SMS/Email)

  

2.  **TOTP Setup Flow**

- Generate secret key and QR code

- User scans QR with authenticator app (Google Authenticator, Authy)

- Display manual entry key for those who can't scan

- User enters 6-digit code from app to verify

- Generate 8 backup codes upon successful verification

- Display backup codes (one-time view with download option)

  

3.  **SMS OTP Setup Flow**

- User enters phone number

- System sends verification code via SMS

- User enters received 6-digit code

- Phone number saved upon successful verification

  

4.  **Email OTP Setup Flow**

- Use registered email or allow email update

- System sends verification code to email

- User enters received 6-digit code

- Email confirmed for 2FA upon successful verification

  

### Subsequent Login with 2FA

1.  **Initial Authentication**: Password/SSO/OIDC login

2.  **2FA Prompt**: Based on user's configured method

3.  **Code Entry**: User enters 6-digit code from their device

4.  **Verification**: System validates code (5-minute validity for OTP)

5.  **Access Granted**: Full session created after successful 2FA

  

### 2FA Recovery Process

1.  **Lost Device**: User clicks "Lost access to 2FA device"

2.  **Recovery Options**:

- Use backup code (TOTP users only)

- Request recovery email to registered address

3.  **Identity Verification**: Additional security questions or admin approval

4.  **Reset 2FA**: User can set up new 2FA method

5.  **Notification**: Email sent about 2FA change for security

  

## 🛠 Model Changes

  

### TenantModel

-  `auth_config` (JSON) - Complete auth configuration
Sample
```json
{
  "password_policy": {
    "min_length": 8,
    "require_uppercase": true,
    "require_lowercase": true,
    "require_numbers": true,
    "require_special_chars": false,
    "password_history_count": 3,
    "password_expiry_days": 90
  },
  "login_methods": {
    "password": {
      "enabled": true,
      "forgot_password_enabled": true,
      "password_reset_link_expiry_hours": 24
    },
    "sso": {
      "enabled": false,
    },
    "oidc": {
      "enabled": false
    }
  },
  "two_factor_auth": {
    "required": false,
    "enforced_from": null,
    "grace_period_days": 7,
    "allowed_methods": [
      "totp",
      "sms",
      "email"
    ],
    "skip_for_sso": false
  },
  "session_policy": {
    "max_concurrent_sessions": 0,
    "force_logout_on_password_change": true
  }
}

```
  

### UserRoleModel

-  `allow_password_auth` - Can disable password login per role

-  `two_factor_required` - Force 2FA for role

-  `allowed_2fa_methods` - Restrict methods per role

-  `password_policy` - Role-specific password rules

  

### AppUserModel

-  `preferred_login_method` - User's preferred auth method

-  `personal_2fa_required` - User can enforce 2FA for themselves

-  `sso_identities` - Linked external accounts

  

## App Panel Changes

  

### App Config

- Password policy settings (length, complexity, expiry)

- Enable/disable login methods globally

- Default 2FA settings and grace periods

  

### Role Management

- Enable/Disable 2FA for role
- Configure login methods 
- Enable/Disable password authentication
- Configure allowed 2FA methods per role
- Set role-specific password policies

  

### User Creation/Edit

- If password disabled for role → Can't set password, set unusable password
- Display 2FA status and requirements
- Show effective configuration from hierarchy

  

## User Profile

- Authentication preferences

- 2FA setup/management 

- Backup code viewing/regeneration

  

## API Changes
	
  - Single LoginAPI in zango core for appauth module
  - Support for 2FA
  - OIDC and SSO to be moved to core
 


## Notes

  

- Users can only make settings MORE restrictive than role/tenant

- Password disabled roles get unusable passwords)

- TOTP secrets encrypted via django-otp

- Backup codes generated once and hashed

- Grace periods for 2FA rollout

 
