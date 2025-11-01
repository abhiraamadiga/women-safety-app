# Onboarding Setup - Gringotts

## Overview
This document describes the onboarding experience implementation with permission requests and ScrollStack card interface.

## Features Implemented

### 1. **Onboarding Page** (`app/templates/onboarding.html`)
- **6-Card ScrollStack Interface**: Pure JavaScript implementation (no React dependencies)
  - Card 1: Welcome to Gringotts
  - Card 2: Security Permissions (Location, Camera, Microphone)
  - Card 3: Smart Safe Routes feature overview
  - Card 4: Instant SOS Alert feature overview
  - Card 5: Report Incidents feature overview
  - Card 6: Community Support with "Enter Gringotts" button

### 2. **Permission Request Flow**
- **Location**: `navigator.geolocation.getCurrentPosition()`
- **Camera**: `navigator.mediaDevices.getUserMedia({ video: true })`
- **Microphone**: `navigator.mediaDevices.getUserMedia({ audio: true })`
- Permission status tracked individually (X/3 granted)
- Results stored in localStorage: `gringotts_permissions`
- Auto-advances to next card on successful grant

### 3. **Navigation Features**
- **Touch/Swipe Support**: Swipe left/right for card navigation
- **Keyboard Support**: Arrow keys (Left/Right/Up/Down)
- **Progress Dots**: Visual indicator at bottom showing current card
- **Smooth Animations**: CSS 3D transforms with transitions

### 4. **Completion Flow**
- Sets localStorage flag: `gringotts_onboarding_complete = 'true'`
- Redirects to main app: `window.location.href = '/'`
- Skip option available (still marks onboarding complete)

### 5. **Branding Update**
All references to "SafeSpace" replaced with "Gringotts":
- `app/templates/landing.html` - Updated hero, features, sections
- `app/templates/base.html` - Updated navbar, meta tags, chat support
- `app/routes.py` - Added `/onboarding` route

## Technical Implementation

### Routes Added (`app/routes.py`)
```python
@bp.route('/onboarding')
def onboarding():
    """Onboarding page with permission requests for first-time users"""
    return render_template('onboarding.html')
```

### Landing Page Check (`app/templates/landing.html`)
```javascript
// Check if onboarding has been completed
if (!localStorage.getItem('gringotts_onboarding_complete')) {
    window.location.href = '/onboarding';
}
```

### Storage Keys
- `gringotts_onboarding_complete`: "true" when onboarding finished
- `gringotts_permissions`: JSON object with permission states

## User Flow

1. **First Visit**: User accesses `https://192.168.137.210:5000/`
2. **Redirect Check**: JavaScript checks localStorage for completion flag
3. **Onboarding**: If not complete, redirects to `/onboarding`
4. **Permission Requests**: User grants location, camera, microphone
5. **Feature Tour**: User navigates through 6 feature cards
6. **Completion**: User clicks "Enter Gringotts" or "Skip Tour"
7. **Main App**: Redirects to `/` and loads main application

## Mobile Compatibility

### HTTPS Requirement
- Permissions APIs require HTTPS connection
- Self-signed certificate must be accepted on mobile device
- Server accessible at: `https://192.168.137.210:5000`

### Safari Specific
- Must include "https://" protocol in URL
- HTTPS-Only mode enabled by default in iOS 15+
- Certificate warning must be accepted (Show Details → visit website)

### Chrome/Android
- Certificate warning: Advanced → Proceed to site
- Permissions automatically prompt on request

## Testing Checklist

- [ ] Clear localStorage: `localStorage.clear()`
- [ ] Access app URL on mobile: `https://192.168.137.210:5000`
- [ ] Accept SSL certificate warning
- [ ] Verify redirect to `/onboarding` page
- [ ] Test permission request for location
- [ ] Test permission request for camera
- [ ] Test permission request for microphone
- [ ] Navigate cards with touch swipes
- [ ] Navigate cards with keyboard arrows
- [ ] Verify progress dots update
- [ ] Click "Enter Gringotts" button
- [ ] Verify redirect to landing page
- [ ] Verify no further onboarding prompts

## File Changes Summary

### New Files
- `app/templates/onboarding.html` - Complete onboarding page

### Modified Files
- `app/routes.py` - Added `/onboarding` route
- `app/templates/landing.html` - Added onboarding check, updated branding
- `app/templates/base.html` - Updated branding (navbar, meta, chat)

## Styling

### Colors
- Primary gradient: `linear-gradient(135deg, #667eea 0%, #764ba2 100%)`
- Cards: White background with border-radius 20px
- Text: Dark gray (#2D3748) for headers, medium gray (#4A5568) for body

### Animations
- Floating icon: `@keyframes float` with translateY
- Card transitions: Transform scale and rotateY
- Progress dots: Scale and opacity changes

## Future Enhancements

- [ ] Add permission denial handling with retry option
- [ ] Implement "Remind me later" functionality
- [ ] Add analytics tracking for onboarding completion rates
- [ ] Implement onboarding version system for updates
- [ ] Add accessibility improvements (ARIA labels, screen reader support)
- [ ] Create admin panel to customize onboarding cards
- [ ] Add multi-language support for onboarding content

## Notes

- **Pure JavaScript**: No React or external libraries required
- **Frontend Only**: No backend changes (as requested by user)
- **Mobile-First**: Designed specifically for mobile sensor access
- **HTTPS Dependent**: All permission APIs require secure context
- **LocalStorage Based**: Simple persistence without database dependency
