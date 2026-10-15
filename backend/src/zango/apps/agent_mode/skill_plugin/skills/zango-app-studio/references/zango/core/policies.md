# Zango Policy Reference

Complete guide for implementing access control and permissions using Zango policies.

## What Are Policies?

Policies in Zango provide fine-grained access control for views, actions, and features.

**Key Features**:
- JSON-based permission definitions
- Control access to views and features
- Assigned to user roles
- Evaluated at runtime to allow or deny access

**Policy Components**:
- **Policy Name**: Unique identifier
- **Description**: Human-readable explanation
- **Statement**: Contains permissions definitions
- **Roles**: List of roles this policy applies to
- **Permissions**: Specific view permissions and features granted

---

## Policy Architecture

```
┌────────────────────────────────────────┐
│      User Role (e.g., "Admin")        │
└────────────┬───────────────────────────┘
             │ has many
             ▼
┌────────────────────────────────────────┐
│         Policies (assigned)            │
│  - PatientCrudViewAccessPolicy         │
│  - PatientCreationPolicy               │
│  - PatientWorkflowPolicy               │
└────────────┬───────────────────────────┘
             │ grants
             ▼
┌────────────────────────────────────────┐
│        Permissions                     │
│  - Can access PatientCrudView          │
│  - Can add patients                    │
│  - Can perform workflow transitions    │
└────────────────────────────────────────┘
```

---

## Creating policies.json

### File Location

**IMPORTANT:** Each module has its own `policies.json` file. The policies.json file should ONLY contain policies for views defined in that specific module.

```
backend/
├── patients/
│   ├── __init__.py
│   ├── views.py          # PatientCrudView defined here
│   └── policies.json     # Policies for PatientCrudView ONLY
├── doctors/
│   ├── __init__.py
│   ├── views.py          # DoctorCrudView defined here
│   └── policies.json     # Policies for DoctorCrudView ONLY
└── appointments/
    ├── __init__.py
    ├── views.py          # AppointmentCrudView defined here
    └── policies.json     # Policies for AppointmentCrudView ONLY
```

**Rule:** If a view is in `backend/patients/views.py`, its policy must be in `backend/patients/policies.json` (NOT in another module's policies.json).

### Basic Structure

```json
{
    "policies": [
        {
            "name": "MyViewAccessPolicy",
            "description": "Access policy for MyView",
            "statement": {
                "permissions": []
            },
            "roles": []
        }
    ]
}
```

---

## View Access Policies

Control which roles can access specific CRUD views.

### Basic View Policy

```json
{
    "name": "PatientCrudViewAccessPolicy",
    "description": "PatientCrudView access policy",
    "statement": {
        "permissions": [
            {
                "name": "backend.patients.views.PatientCrudView",
                "type": "view",
                "features": [
                    "add",
                    "download"
                ]
            }
        ]
    },
    "roles": [
        "Admin"
    ]
}
```

**Policy Breakdown**:
- **name**: Unique policy identifier
- **description**: Human-readable description
- **permissions[].name**: Full Python path to the view class
- **permissions[].type**: Always `"view"` for view policies
- **permissions[].features**: Array of features to enable
- **roles**: Array of role names that get this policy

### Package-Specific Features

The `features` array contains package-specific permissions. Each package defines its own features.

**Note**: Features are defined by the package, not by the policy system. Refer to package-specific documentation:
- CRUD package features → See `packages/crud/views/core.md`
- Other package features → See respective package documentation

### View-Only Policy

```json
{
    "name": "PatientCrudViewAccessPolicyViewOnly",
    "description": "PatientCrudView access policy view only",
    "statement": {
        "permissions": [
            {
                "name": "backend.patients.views.PatientCrudView",
                "type": "view",
                "features": [
                    "download"
                ]
            }
        ]
    },
    "roles": [
        "Doctor",
        "Nurse"
    ]
}
```

This policy allows viewing and downloading but NOT adding new records.

---

## Complete Policy Examples

### Example 1: Admin vs Regular User

```json
{
    "policies": [
        {
            "name": "AdminFullAccess",
            "description": "Full access for administrators",
            "statement": {
                "permissions": [
                    {
                        "name": "backend.patients.views.PatientCrudView",
                        "type": "view",
                        "features": ["add", "download", "upload"]
                    }
                ]
            },
            "roles": ["Admin"]
        },
        {
            "name": "UserViewOnly",
            "description": "View-only access for regular users",
            "statement": {
                "permissions": [
                    {
                        "name": "backend.patients.views.PatientCrudView",
                        "type": "view",
                        "features": ["download"]
                    }
                ]
            },
            "roles": ["Doctor", "Nurse"]
        }
    ]
}
```

### Example 2: Multiple Views Access

```json
{
    "name": "ManagerAccessPolicy",
    "description": "Access to multiple views for managers",
    "statement": {
        "permissions": [
            {
                "name": "backend.patients.views.PatientCrudView",
                "type": "view",
                "features": ["add", "download"]
            },
            {
                "name": "backend.appointments.views.AppointmentCrudView",
                "type": "view",
                "features": ["add", "download"]
            }
        ]
    },
    "roles": ["Manager", "Team Lead"]
}
```

### Example 3: Department-Specific Access

```json
{
    "name": "LabTechnicianAccessPolicy",
    "description": "Views accessible only to Lab technicians",
    "statement": {
        "permissions": [
            {
                "name": "backend.lab.views.TestResultCrudView",
                "type": "view",
                "features": ["add", "download", "upload"]
            }
        ]
    },
    "roles": ["Lab Technician", "Lab Manager"]
}
```

### Example 4: Complete Module Policies

```json
{
    "policies": [
        {
            "name": "PatientCrudViewAccessPolicy",
            "description": "PatientCrudView access policy with full permissions",
            "statement": {
                "permissions": [
                    {
                        "name": "backend.patients.views.PatientCrudView",
                        "type": "view",
                        "features": [
                            "add",
                            "download"
                        ]
                    }
                ]
            },
            "roles": [
                "Admin"
            ]
        },
        {
            "name": "PatientCrudViewAccessPolicyViewOnly",
            "description": "PatientCrudView access policy view only",
            "statement": {
                "permissions": [
                    {
                        "name": "backend.patients.views.PatientCrudView",
                        "type": "view",
                        "features": [
                            "download"
                        ]
                    }
                ]
            },
            "roles": [
                "Doctor",
                "Nurse",
                "Receptionist"
            ]
        },
        {
            "name": "PatientCreationPolicy",
            "description": "Policy for creating new patients",
            "statement": {
                "permissions": [
                    {
                        "name": "backend.patients.views.PatientCrudView",
                        "type": "view",
                        "features": [
                            "add"
                        ]
                    }
                ]
            },
            "roles": [
                "Admin",
                "Receptionist"
            ]
        }
    ]
}
```

---

## Policy Registration

### Syncing Policies

**CRITICAL**: After creating or updating `policies.json`, you MUST sync policies via the API for changes to take effect.

**Sync via API**:
```bash
curl -s -b /tmp/zango_cookies -X POST \
  "http://localhost:8000/api/v1/apps/$APP_UUID/policies/?action=sync_policies" \
  -H "X-CSRFToken: $CSRF" \
  -H "Referer: http://localhost:8000/platform/" \
  -H "Content-Type: multipart/form-data; boundary=----WebKitFormBoundary" \
  --data-raw '------WebKitFormBoundary--'
```

See [app-panel-api.md](../app-panel-api.md) for full details on the sync policies API.

**What Happens During Sync**:
- Policies from `policies.json` files are loaded
- New policies are created in the database
- Existing policies are updated
- Policies become available for role assignment

**When to Sync**:
- After creating new `policies.json` file
- After adding new policies to existing file
- After modifying policy permissions or features
- After changing policy roles

⚠️ **Important**: Policies will NOT work until synced. Always sync after any policy changes.

### Manual Assignment via App Panel

After syncing, assign policies to roles:

1. Navigate to **User Roles** in App Panel
2. Select a role
3. Click **"Edit"** or **"Policies"**
4. Select policies to assign
5. Save changes

---

## Common Policy Patterns

### Pattern 1: Role-Based Feature Access

Different features for different roles:

```json
{
    "policies": [
        {
            "name": "AdminPatientPolicy",
            "statement": {
                "permissions": [
                    {
                        "name": "backend.patients.views.PatientCrudView",
                        "type": "view",
                        "features": ["add", "download", "upload"]
                    }
                ]
            },
            "roles": ["Admin"]
        },
        {
            "name": "DoctorPatientPolicy",
            "statement": {
                "permissions": [
                    {
                        "name": "backend.patients.views.PatientCrudView",
                        "type": "view",
                        "features": ["add", "download"]
                    }
                ]
            },
            "roles": ["Doctor"]
        },
        {
            "name": "NursePatientPolicy",
            "statement": {
                "permissions": [
                    {
                        "name": "backend.patients.views.PatientCrudView",
                        "type": "view",
                        "features": ["download"]
                    }
                ]
            },
            "roles": ["Nurse"]
        }
    ]
}
```

### Pattern 2: Hierarchical Permissions

Manager has all permissions that employees have:

```json
{
    "policies": [
        {
            "name": "EmployeeBasePolicy",
            "statement": {
                "permissions": [
                    {
                        "name": "backend.patients.views.PatientCrudView",
                        "type": "view",
                        "features": ["download"]
                    }
                ]
            },
            "roles": ["Employee", "Manager", "Admin"]
        },
        {
            "name": "ManagerExtendedPolicy",
            "statement": {
                "permissions": [
                    {
                        "name": "backend.patients.views.PatientCrudView",
                        "type": "view",
                        "features": ["add"]
                    }
                ]
            },
            "roles": ["Manager", "Admin"]
        }
    ]
}
```

### Pattern 3: Module-Specific Policies

Separate policies per module:

```python
# backend/patients/policies.json
{
    "policies": [
        {
            "name": "PatientModuleAccessPolicy",
            "statement": {
                "permissions": [
                    {
                        "name": "backend.patients.views.PatientCrudView",
                        "type": "view",
                        "features": ["add", "download"]
                    }
                ]
            },
            "roles": ["Doctor", "Admin"]
        }
    ]
}
```

```python
# backend/appointments/policies.json
{
    "policies": [
        {
            "name": "AppointmentModuleAccessPolicy",
            "statement": {
                "permissions": [
                    {
                        "name": "backend.appointments.views.AppointmentCrudView",
                        "type": "view",
                        "features": ["add", "download"]
                    }
                ]
            },
            "roles": ["Receptionist", "Admin"]
        }
    ]
}
```

---

## Best Practices

### 1. Naming Conventions

```
- Use descriptive names: PatientCrudViewAccessPolicy
- Suffix with purpose: ViewAccessPolicy, ViewAccessPolicyViewOnly
- Use consistent prefixes: <Module><Purpose>Policy
```

**Examples**:
- `PatientCrudViewAccessPolicy` - Full access
- `PatientCrudViewAccessPolicyViewOnly` - View-only access
- `PatientCreationPolicy` - Creation permission
- `PatientDeletePolicy` - Deletion permission

### 2. Granularity

- Create separate policies for different access levels
- Don't create one giant policy for everything
- Group related permissions logically

**Good**:
```json
{
    "policies": [
        {"name": "PatientViewPolicy", "roles": ["Doctor", "Nurse"]},
        {"name": "PatientEditPolicy", "roles": ["Doctor"]},
        {"name": "PatientDeletePolicy", "roles": ["Admin"]}
    ]
}
```

**Avoid**:
```json
{
    "policies": [
        {"name": "AllPermissionsPolicy", "roles": ["Everyone"]}
    ]
}
```

### 3. Documentation

- Always provide clear descriptions
- Document which roles should have each policy
- Explain what permissions grant

```json
{
    "name": "PatientCrudViewAccessPolicy",
    "description": "Full access to PatientCrudView including add and download features. Assigned to Admin role for complete patient management.",
    "statement": {...},
    "roles": ["Admin"]
}
```

### 4. Testing

- Test with different roles
- Verify buttons show/hide correctly
- Confirm actions are allowed/denied properly
- Test edge cases (no role, multiple roles)

---

## Troubleshooting

### Policy Not Working

**Problem**: Policy defined but permissions not applying

**Solutions**:
- **Call sync policies API** (most common issue!)
- Check policy is assigned to the role in App Panel
- Verify policy name matches exactly in code
- Confirm role is active
- Check view path is correct (full Python path)

### Features Not Working

**Problem**: Policy has features but they're not working

**Solutions**:
- Verify features are correct for the package (see package docs)
- Call sync policies API
- Check role has the policy assigned
- Confirm user has active role

### Invalid JSON in policies.json

**Problem**: Application not loading policies

**Solutions**:
- Validate JSON syntax (no trailing commas)
- Use double quotes, not single quotes
- Check all brackets and braces are balanced
- Use a JSON validator tool

---

## Summary

**Quick Checklist**:
- [ ] Create `policies.json` in module
- [ ] Define policies with unique names
- [ ] Specify full view path in permissions
- [ ] List package-specific features (see package docs)
- [ ] Assign to appropriate roles
- [ ] **Call sync policies API** (CRITICAL!)
- [ ] Test with different roles
- [ ] Verify policies are loaded and assigned in App Panel
