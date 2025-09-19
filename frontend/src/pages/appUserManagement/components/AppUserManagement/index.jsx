import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import useApi from '../../../../hooks/useApi';
import BreadCrumbs from '../../../app/components/BreadCrumbs';
import {
	openIsAddNewUserModalOpen,
	openIsEditUserDetailModalOpen,
	openIsDeactivateUserModalOpen,
	openIsActivateUserModalOpen,
	openIsResetPasswordModalOpen,
	selectAppUserManagementData,
	selectRerenderPage,
	setAppUserManagementData,
} from '../../slice';
import ActivateUserModal from '../Modals/ActivateUserModal';
import AddNewUserModal from '../Modals/AddNewUserModal';
import DeactivateUserModal from '../Modals/DeactivateUserModal';
import EditUserDetailsModal from '../Modals/EditUserDetailsModal';
import ResetPasswordModal from '../Modals/ResetPasswordModal';

export default function AppUserManagement() {
	const { appId } = useParams();
	const dispatch = useDispatch();
	const triggerApi = useApi();
	
	const rerenderPage = useSelector(selectRerenderPage);
	const appUserManagementData = useSelector(selectAppUserManagementData);
	
	const [loading, setLoading] = useState(true);
	const [searchTerm, setSearchTerm] = useState('');
	const [filters, setFilters] = useState({
		is_active: '',
		role: ''
	});
	const [page, setPage] = useState(1);
	const [pageSize] = useState(20);
	const [totalPages, setTotalPages] = useState(1);
	const [expandedRows, setExpandedRows] = useState({});

	const handleAddNewUser = () => {
		dispatch(openIsAddNewUserModalOpen());
	};

	const updateAppUserManagementData = (value) => {
		dispatch(setAppUserManagementData(value));
	};

	// Fetch users data
	const fetchUsers = async () => {
		setLoading(true);
		try {
			const queryParams = new URLSearchParams({
				page: page.toString(),
				page_size: pageSize.toString(),
				include_dropdown_options: 'true',
				search: searchTerm,
			});

			// Add filters
			if (filters.is_active !== '') {
				queryParams.append('search_is_active', filters.is_active);
			}
			if (filters.role) {
				queryParams.append('search_role', filters.role);
			}

			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/users/?${queryParams.toString()}`,
				type: 'GET',
				loader: false,
			});

			if (success && response) {
				updateAppUserManagementData(response);
				setTotalPages(response.users?.total_pages || 1);
			}
		} catch (error) {
			console.error('Error fetching users:', error);
		} finally {
			setLoading(false);
		}
	};

	useEffect(() => {
		fetchUsers();
	}, [appId, page, searchTerm, filters, rerenderPage]);

	// Toggle row expansion
	const toggleRowExpansion = (userId) => {
		setExpandedRows(prev => ({
			...prev,
			[userId]: !prev[userId]
		}));
	};

	// Format date
	const formatDate = (dateString) => {
		if (!dateString) return '-';
		const date = new Date(dateString);
		const now = new Date();
		const diffMs = now - date;
		const diffDays = Math.floor(diffMs / 86400000);
		
		if (diffDays === 0) return 'Today';
		if (diffDays === 1) return 'Yesterday';
		if (diffDays < 7) return `${diffDays} days ago`;
		
		return date.toLocaleDateString();
	};

	const users = appUserManagementData?.users?.records || [];
	const roles = appUserManagementData?.dropdown_options?.role || [];

	return (
		<>
			<div className="flex flex-col h-full bg-[#F8FAFC] overflow-hidden">
				{/* Header */}
				<div className="bg-white border-b border-[#E5E7EB] px-[40px] py-[20px] flex-shrink-0">
					<div className="flex items-center justify-between">
						<div>
							<BreadCrumbs />
							<div className="flex items-center gap-[12px] mt-[8px]">
								<div className="flex h-[40px] w-[40px] items-center justify-center rounded-[8px] bg-gradient-to-br from-[#5048ED] to-[#346BD4] shadow-lg">
									<svg width="24" height="24" viewBox="0 0 24 24" fill="none">
										<path d="M17 21V19C17 17.9391 16.5786 16.9217 15.8284 16.1716C15.0783 15.4214 14.0609 15 13 15H5C3.93913 15 2.92172 15.4214 2.17157 16.1716C1.42143 16.9217 1 17.9391 1 19V21M13 7C13 9.20914 11.2091 11 9 11C6.79086 11 5 9.20914 5 7C5 4.79086 6.79086 3 9 3C11.2091 3 13 4.79086 13 7ZM23 21V19C22.9993 18.1137 22.7044 17.2528 22.1614 16.5523C21.6184 15.8519 20.8581 15.3516 20 15.13M16 3.13C16.8604 3.3503 17.623 3.8507 18.1676 4.55231C18.7122 5.25392 19.0078 6.11683 19.0078 7.005C19.0078 7.89317 18.7122 8.75608 18.1676 9.45769C17.623 10.1593 16.8604 10.6597 16 10.88" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
									</svg>
								</div>
								<div>
									<h1 className="font-source-sans-pro text-[24px] font-semibold leading-[32px] text-[#111827]">
										User Management
									</h1>
									<p className="font-lato text-[14px] leading-[20px] text-[#6B7280]">
										Manage your application users and their access
									</p>
								</div>
							</div>
						</div>
					</div>
				</div>

				{/* Content */}
				<div className="flex-1 px-[40px] py-[32px] bg-[#F8FAFC] overflow-y-auto">
					<div className="space-y-6">
							{/* Stats Cards */}
							<div className="grid grid-cols-1 md:grid-cols-4 gap-4">
							<div className="rounded-lg border bg-card p-6 transition-colors hover:bg-accent/5">
								<div className="flex items-center justify-between">
									<div>
										<p className="text-sm font-medium text-muted-foreground">Total Users</p>
										<p className="text-2xl font-medium tracking-tight mt-1">{users.length}</p>
									</div>
									<div className="p-3 bg-primary/10 rounded-md">
										<svg width="24" height="24" viewBox="0 0 24 24" fill="none" className="text-primary">
											<path d="M17 21V19C17 17.9391 16.5786 16.9217 15.8284 16.1716C15.0783 15.4214 14.0609 15 13 15H5C3.93913 15 2.92172 15.4214 2.17157 16.1716C1.42143 16.9217 1 17.9391 1 19V21M13 7C13 9.20914 11.2091 11 9 11C6.79086 11 5 9.20914 5 7C5 4.79086 6.79086 3 9 3C11.2091 3 13 4.79086 13 7ZM23 21V19C22.9993 18.1137 22.7044 17.2528 22.1614 16.5523C21.6184 15.8519 20.8581 15.3516 20 15.13M16 3.13C16.8604 3.3503 17.623 3.8507 18.1676 4.55231C18.7122 5.25392 19.0078 6.11683 19.0078 7.005C19.0078 7.89317 18.7122 8.75608 18.1676 9.45769C17.623 10.1593 16.8604 10.6597 16 10.88" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
										</svg>
									</div>
								</div>
							</div>

							<div className="rounded-lg border bg-card p-6 transition-colors hover:bg-accent/5">
								<div className="flex items-center justify-between">
									<div>
										<p className="text-sm font-medium text-muted-foreground">Active Users</p>
										<p className="text-2xl font-medium tracking-tight text-emerald-600 dark:text-emerald-400 mt-1">
											{users.filter(user => user.is_active).length}
										</p>
									</div>
									<div className="p-3 bg-emerald-500/10 rounded-md">
										<svg width="24" height="24" viewBox="0 0 24 24" fill="none" className="text-emerald-600 dark:text-emerald-400">
											<circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"/>
											<path d="M8 12L11 15L16 10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
										</svg>
									</div>
								</div>
							</div>

							<div className="rounded-lg border bg-card p-6 transition-colors hover:bg-accent/5">
								<div className="flex items-center justify-between">
									<div>
										<p className="text-sm font-medium text-muted-foreground">Inactive Users</p>
										<p className="text-2xl font-medium tracking-tight text-red-600 dark:text-red-400 mt-1">
											{users.filter(user => !user.is_active).length}
										</p>
									</div>
									<div className="p-3 bg-red-500/10 rounded-md">
										<svg width="24" height="24" viewBox="0 0 24 24" fill="none" className="text-red-600 dark:text-red-400">
											<circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"/>
											<path d="M15 9L9 15M9 9L15 15" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
										</svg>
									</div>
								</div>
							</div>

							<div className="rounded-lg border bg-card p-6 transition-colors hover:bg-accent/5">
								<div className="flex items-center justify-between">
									<div>
										<p className="text-sm font-medium text-muted-foreground">Roles Assigned</p>
										<p className="text-2xl font-medium tracking-tight text-purple-600 dark:text-purple-400 mt-1">
											{roles.length}
										</p>
									</div>
									<div className="p-3 bg-purple-500/10 rounded-md">
										<svg width="24" height="24" viewBox="0 0 24 24" fill="none" className="text-purple-600 dark:text-purple-400">
											<path d="M12 15C15.866 15 19 11.866 19 8C19 4.13401 15.866 1 12 1C8.13401 1 5 4.13401 5 8C5 11.866 8.13401 15 12 15Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
											<path d="M8.21 13.89L7 23L12 20L17 23L15.79 13.88" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
										</svg>
									</div>
								</div>
							</div>
							</div>

							{/* Filters and Search */}
							<div className="rounded-lg border bg-card p-6">
								<div className="flex flex-wrap gap-2">
									{/* Search */}
									<div className="relative">
										<input
											type="text"
											placeholder="Search users..."
											value={searchTerm}
											onChange={(e) => setSearchTerm(e.target.value)}
											className="h-9 w-full sm:w-64 rounded-md border bg-background px-3 py-1 text-sm pl-9 placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
										/>
										<svg
											className="absolute left-2.5 top-2 h-4 w-4 text-muted-foreground"
											fill="none"
											viewBox="0 0 24 24"
											stroke="currentColor"
										>
											<path
												strokeLinecap="round"
												strokeLinejoin="round"
												strokeWidth={2}
												d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
											/>
										</svg>
									</div>

									{/* Status Filter */}
									<select
								value={filters.is_active}
								onChange={(e) => setFilters({ ...filters, is_active: e.target.value })}
								className="h-9 rounded-md border bg-background px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
							>
										<option value="">All Status</option>
										<option value="true">Active</option>
										<option value="false">Inactive</option>
									</select>

									{/* Role Filter */}
									<select
								value={filters.role}
								onChange={(e) => setFilters({ ...filters, role: e.target.value })}
								className="h-9 rounded-md border bg-background px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
							>
										<option value="">All Roles</option>
										{roles.map(role => (
											<option key={role.id} value={role.id}>{role.label}</option>
										))}
									</select>

									{/* Add User Button */}
									<button
								onClick={handleAddNewUser}
								className="inline-flex items-center gap-2 h-9 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50"
							>
										<svg width="16" height="16" viewBox="0 0 16 16" fill="none">
											<path d="M8 1V15M1 8H15" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
										</svg>
										Add User
									</button>
								</div>
							</div>

							{/* Users List */}
							<div className="space-y-4">
								{loading ? (
									<div className="rounded-lg border bg-card p-12">
							<div className="flex items-center justify-center">
								<div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
							</div>
						</div>
								) : users.length === 0 ? (
									<div className="rounded-lg border bg-card p-12 text-center">
							<svg
								className="mx-auto h-12 w-12 text-muted-foreground/50"
								fill="none"
								viewBox="0 0 24 24"
								stroke="currentColor"
							>
								<path
									strokeLinecap="round"
									strokeLinejoin="round"
									strokeWidth={1.5}
									d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
								/>
							</svg>
							<p className="mt-2 text-sm text-muted-foreground">No users found</p>
							<button
								onClick={handleAddNewUser}
								className="mt-4 inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
							>
								<svg width="16" height="16" viewBox="0 0 16 16" fill="none">
									<path d="M8 1V15M1 8H15" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
								</svg>
								Create First User
							</button>
						</div>
					) : (
						<UsersList
							users={users}
							expandedRows={expandedRows}
							toggleRowExpansion={toggleRowExpansion}
							formatDate={formatDate}
						/>
					)}
				</div>

							{/* Pagination */}
							{totalPages > 1 && (
								<div className="rounded-lg border bg-card px-6 py-3 flex items-center justify-between">
						<div className="flex items-center gap-2">
							<button
								onClick={() => setPage(p => Math.max(1, p - 1))}
								disabled={page === 1}
								className="h-8 w-8 rounded-md border bg-background hover:bg-accent hover:text-accent-foreground disabled:opacity-50 disabled:cursor-not-allowed transition-colors inline-flex items-center justify-center"
							>
								<svg width="16" height="16" viewBox="0 0 16 16" fill="none">
									<path d="M10 12L6 8L10 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
								</svg>
							</button>
							<span className="text-sm text-muted-foreground">
								Page {page} of {totalPages}
							</span>
							<button
								onClick={() => setPage(p => Math.min(totalPages, p + 1))}
								disabled={page === totalPages}
								className="h-8 w-8 rounded-md border bg-background hover:bg-accent hover:text-accent-foreground disabled:opacity-50 disabled:cursor-not-allowed transition-colors inline-flex items-center justify-center"
							>
								<svg width="16" height="16" viewBox="0 0 16 16" fill="none">
									<path d="M6 12L10 8L6 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
								</svg>
							</button>
						</div>
						<span className="text-sm text-muted-foreground">
							Showing {users.length} of {totalPages * pageSize} users
						</span>
								</div>
							)}
						</div>
					</div>
				</div>

			{/* Modals */}
			<AddNewUserModal />
			<EditUserDetailsModal />
			<DeactivateUserModal />
			<ActivateUserModal />
			<ResetPasswordModal />
		</>
	);
}

// Users List Component
function UsersList({ users, expandedRows, toggleRowExpansion, formatDate }) {
	return (
		<>
			{users.map((user) => {
				const isExpanded = expandedRows[user.id];
				
				return (
					<UserCard
						key={user.id}
						user={user}
						isExpanded={isExpanded}
						toggleExpansion={toggleRowExpansion}
						formatDate={formatDate}
					/>
				);
			})}
		</>
	);
}

// User Card Component
function UserCard({ user, isExpanded, toggleExpansion, formatDate }) {
	const dispatch = useDispatch();

	const handleEdit = () => {
		dispatch(openIsEditUserDetailModalOpen(user));
	};

	const handleToggleStatus = () => {
		if (user.is_active) {
			dispatch(openIsDeactivateUserModalOpen(user));
		} else {
			dispatch(openIsActivateUserModalOpen(user));
		}
	};

	const handleResetPassword = () => {
		dispatch(openIsResetPasswordModalOpen(user));
	};

	return (
		<div className="rounded-lg border bg-card overflow-hidden transition-all hover:shadow-md">
			<div
				className="p-6 cursor-pointer"
				onClick={() => toggleExpansion(user.id)}
			>
				<div className="flex items-start justify-between">
					<div className="flex items-start gap-4">
						{/* User Avatar */}
						<div className="w-12 h-12 bg-gradient-to-br from-primary to-primary/60 rounded-full flex items-center justify-center text-primary-foreground font-semibold">
							{user.name ? user.name.charAt(0).toUpperCase() : 'U'}
						</div>

						{/* User Info */}
						<div className="space-y-2">
							<div className="flex items-center gap-3">
								<h3 className="font-medium text-lg">{user.name}</h3>
								<span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${
									user.is_active
										? 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/20'
										: 'bg-red-500/10 text-red-700 dark:text-red-400 border border-red-500/20'
								}`}>
									<span className={`w-1.5 h-1.5 rounded-full ${user.is_active ? 'bg-emerald-600' : 'bg-red-600'}`}></span>
									{user.is_active ? 'Active' : 'Inactive'}
								</span>
							</div>
							
							<div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
								<span className="flex items-center gap-1">
									<svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor" className="opacity-50">
										<path d="M3 5a2 2 0 012-2h6a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2V5zm4 1a1 1 0 100 2h2a1 1 0 100-2H7z"/>
									</svg>
									ID: {user.id}
								</span>
								<span className="flex items-center gap-1">
									<svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor" className="opacity-50">
										<path d="M2.5 3.5a.5.5 0 010-1h11a.5.5 0 010 1h-11zm0 3a.5.5 0 010-1h11a.5.5 0 010 1h-11zm0 3a.5.5 0 010-1h11a.5.5 0 010 1h-11zm0 3a.5.5 0 010-1h11a.5.5 0 010 1h-11z"/>
									</svg>
									{user.email}
								</span>
								{user.mobile && (
									<span className="flex items-center gap-1">
										<svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor" className="opacity-50">
											<path d="M11 1a1 1 0 011 1v12a1 1 0 01-1 1H5a1 1 0 01-1-1V2a1 1 0 011-1h6zM5 0a2 2 0 00-2 2v12a2 2 0 002 2h6a2 2 0 002-2V2a2 2 0 00-2-2H5z"/>
											<path d="M8 14a1 1 0 100-2 1 1 0 000 2z"/>
										</svg>
										{user.mobile}
									</span>
								)}
							</div>

							{/* Roles */}
							{user.roles && user.roles.length > 0 && (
								<div className="flex flex-wrap gap-2 mt-2">
									{user.roles.map((role, idx) => (
										<span key={idx} className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-primary/10 text-primary border border-primary/20">
											{role.name || role}
										</span>
									))}
								</div>
							)}
						</div>
					</div>

					{/* Actions and Expand Icon */}
					<div className="flex items-center gap-2">
						{/* Action Buttons */}
						<div className="flex gap-1" onClick={(e) => e.stopPropagation()}>
							<button
								onClick={handleEdit}
								className="p-2 rounded-md hover:bg-accent hover:text-accent-foreground transition-colors"
								title="Edit User"
							>
								<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
									<path d="M15.502 1.94a.5.5 0 010 .706L14.459 3.69l-2-2L13.502.646a.5.5 0 01.707 0l1.293 1.293zm-1.75 2.456l-2-2L4.939 9.21a.5.5 0 00-.121.196l-.805 2.414a.25.25 0 00.316.316l2.414-.805a.5.5 0 00.196-.12l6.813-6.814z"/>
								</svg>
							</button>
							<button
								onClick={handleResetPassword}
								className="p-2 rounded-md hover:bg-accent hover:text-accent-foreground transition-colors"
								title="Reset Password"
							>
								<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
									<path d="M3 5v6h6a4 4 0 000-8 3.99 3.99 0 00-2.906 1.258l-.094.101V2a5.972 5.972 0 011.416-.81A5.967 5.967 0 019 1a6 6 0 016 6 6 6 0 01-6 6H3V5z"/>
									<path d="M1.5 5.5a.5.5 0 10-1 0v3a.5.5 0 001 0v-3zm1.5 0a.5.5 0 10-1 0v3a.5.5 0 001 0v-3z"/>
								</svg>
							</button>
							<button
								onClick={handleToggleStatus}
								className={`p-2 rounded-md transition-colors ${
									user.is_active
										? 'hover:bg-red-100 hover:text-red-600 dark:hover:bg-red-900/20 dark:hover:text-red-400'
										: 'hover:bg-emerald-100 hover:text-emerald-600 dark:hover:bg-emerald-900/20 dark:hover:text-emerald-400'
								}`}
								title={user.is_active ? 'Deactivate User' : 'Activate User'}
							>
								{user.is_active ? (
									<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
										<path d="M8 15A7 7 0 118 1a7 7 0 010 14zm0 1A8 8 0 108 0a8 8 0 000 16z"/>
										<path d="M4.646 4.646a.5.5 0 01.708 0L8 7.293l2.646-2.647a.5.5 0 01.708.708L8.707 8l2.647 2.646a.5.5 0 01-.708.708L8 8.707l-2.646 2.647a.5.5 0 01-.708-.708L7.293 8 4.646 5.354a.5.5 0 010-.708z"/>
									</svg>
								) : (
									<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
										<path d="M8 15A7 7 0 118 1a7 7 0 010 14zm0 1A8 8 0 108 0a8 8 0 000 16z"/>
										<path d="M10.97 4.97a.235.235 0 00-.02.022L7.477 9.417 5.384 7.323a.75.75 0 00-1.06 1.06L6.97 11.03a.75.75 0 001.079-.02l3.992-4.99a.75.75 0 00-1.071-1.05z"/>
									</svg>
								)}
							</button>
						</div>

						{/* Expand Icon */}
						<svg
							className={`h-4 w-4 text-muted-foreground transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`}
							fill="none"
							viewBox="0 0 24 24"
							stroke="currentColor"
						>
							<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
						</svg>
					</div>
				</div>
			</div>

			{/* Expanded Details */}
			{isExpanded && (
				<div className="border-t bg-muted/50 p-6">
					<div className="grid grid-cols-1 md:grid-cols-2 gap-6">
						<div>
							<h4 className="text-sm font-medium mb-3">Access Information</h4>
							<div className="space-y-2">
								<div className="flex justify-between text-sm">
									<span className="text-muted-foreground">Last Login:</span>
									<span>{formatDate(user.last_login)}</span>
								</div>
								<div className="flex justify-between text-sm">
									<span className="text-muted-foreground">Date Joined:</span>
									<span>{formatDate(user.created_at)}</span>
								</div>
								<div className="flex justify-between text-sm">
									<span className="text-muted-foreground">Password Changed:</span>
									<span>{formatDate(user.password_change_at)}</span>
								</div>
							</div>
						</div>

						<div>
							<h4 className="text-sm font-medium mb-3">Contact Details</h4>
							<div className="space-y-2">
								<div className="text-sm">
									<span className="text-muted-foreground block mb-1">Email Address:</span>
									<span className="font-mono">{user.email}</span>
								</div>
								{user.mobile && (
									<div className="text-sm">
										<span className="text-muted-foreground block mb-1">Mobile Number:</span>
										<span className="font-mono">{user.mobile}</span>
									</div>
								)}
							</div>
						</div>
					</div>
				</div>
			)}
		</div>
	);
}