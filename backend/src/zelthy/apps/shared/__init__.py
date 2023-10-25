"""
    Django apps are organized in this folder structure:
        
        backend/apps/shared/: houses apps that represent shared functionality such as 
        Tenancy Management, Platform users, etc. Tables of these apps are created in 
        public schema in the database.

        Other apps that are created inside backend/apps represent tenant features and 
        as such the models exposed by these apps are created in tenant schema.
"""


