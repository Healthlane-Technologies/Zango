import { useQuery } from '@tanstack/react-query';
import { api } from './client';

// PlatformUserSerializerModel (api/platform/auth/v1/serializers.py), trimmed to what the shell shows.
export interface Me {
	id: number;
	name: string;
	email: string;
	is_superadmin: boolean;
}

export function useMe() {
	return useQuery({
		queryKey: ['me'],
		queryFn: () =>
			api<{ app_data: { user_logged_in: Me } }>('/api/v1/auth/app-initalization-details/').then(
				(r) => r.app_data.user_logged_in,
			),
		staleTime: Infinity,
	});
}
