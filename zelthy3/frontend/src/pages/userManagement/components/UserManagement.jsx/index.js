import BreadCrumbs from '../BreadCrumbs';
import { useSelector, useDispatch } from 'react-redux';
import { open } from '../../slice';
import AddNewUserModal from '../Models/AddNewUserModal';
import { ReactComponent as AddUserIcon } from '../../../../assets/images/svg/add-user-icon.svg';
import Table from '../Table';

export default function UserManagement() {
	const dispatch = useDispatch();

	const handleAddNewUser = () => {
		dispatch(open());
	};
	return (
		<>
			<div className="flex grow flex-col gap-[20px]">
				<div className="flex items-center justify-between py-[12px] pl-[40px] pr-[48px]">
					<BreadCrumbs />
					<button
						type="button"
						onClick={handleAddNewUser}
						className="flex gap-[8px] rounded-[4px] bg-primary px-[16px] py-[7px]"
					>
						<span className="font-lato text-[14px] font-bold leading-[20px] text-[#FFFFFF]">
							New User
						</span>
						<AddUserIcon />
					</button>
				</div>
				<div className="flex grow flex-col overflow-x-auto">
					<Table
						tableData={[
							{
								user_name: 'Jenny Wilson',
								user_id: 5045,
								id: 12,
								mobile: 9876543121,
								email: 'cameron.williamson@email.com',
								role_access: ['Role 1'],
								policy: ['Policy 1'],
								last_login_date_joined: '21 Sep, 2020',
							},
							{
								user_name: 'Jenny Wilson',
								user_id: 5043,
								id: 11,
								mobile: 9876543121,
								email: 'diannerussell@email.com',
								role_access: ['Role 1'],
								policy: ['Policy 1'],
								last_login_date_joined: '21 Sep, 2020',
							},
							{
								user_name: 'Jenny Wilson',
								user_id: 5043,
								id: 11,
								mobile: 9876543121,
								email: 'diannerussell@email.com',
								role_access: ['Role 1'],
								policy: ['Policy 1'],
								last_login_date_joined: '21 Sep, 2020',
							},
							{
								user_name: 'Jenny Wilson',
								user_id: 5043,
								id: 11,
								mobile: 9876543121,
								email: 'diannerussell@email.com',
								role_access: ['Role 1'],
								policy: ['Policy 1'],
								last_login_date_joined: '21 Sep, 2020',
							},
							{
								user_name: 'Jenny Wilson',
								user_id: 5043,
								id: 11,
								mobile: 9876543121,
								email: 'diannerussell@email.com',
								role_access: ['Role 1'],
								policy: ['Policy 1'],
								last_login_date_joined: '21 Sep, 2020',
							},
							{
								user_name: 'Jenny Wilson',
								user_id: 5043,
								id: 11,
								mobile: 9876543121,
								email: 'diannerussell@email.com',
								role_access: ['Role 1'],
								policy: ['Policy 1'],
								last_login_date_joined: '21 Sep, 2020',
							},
							{
								user_name: 'Jenny Wilson',
								user_id: 5043,
								id: 11,
								mobile: 9876543121,
								email: 'diannerussell@email.com',
								role_access: ['Role 1'],
								policy: ['Policy 1'],
								last_login_date_joined: '21 Sep, 2020',
							},
							{
								user_name: 'Jenny Wilson',
								user_id: 5043,
								id: 11,
								mobile: 9876543121,
								email: 'diannerussell@email.com',
								role_access: ['Role 1'],
								policy: ['Policy 1'],
								last_login_date_joined: '21 Sep, 2020',
							},
							{
								user_name: 'Jenny Wilson',
								user_id: 5043,
								id: 11,
								mobile: 9876543121,
								email: 'diannerussell@email.com',
								role_access: ['Role 1'],
								policy: ['Policy 1'],
								last_login_date_joined: '21 Sep, 2020',
							},
							{
								user_name: 'Jenny Wilson',
								user_id: 5043,
								id: 11,
								mobile: 9876543121,
								email: 'diannerussell@email.com',
								role_access: ['Role 1'],
								policy: ['Policy 1'],
								last_login_date_joined: '21 Sep, 2020',
							},
							{
								user_name: 'Jenny Wilson',
								user_id: 5043,
								id: 11,
								mobile: 9876543121,
								email: 'diannerussell@email.com',
								role_access: ['Role 1'],
								policy: ['Policy 1'],
								last_login_date_joined: '21 Sep, 2020',
							},
							{
								user_name: 'Jenny Wilson',
								user_id: 5043,
								id: 11,
								mobile: 9876543121,
								email: 'diannerussell@email.com',
								role_access: ['Role 1'],
								policy: ['Policy 1'],
								last_login_date_joined: '21 Sep, 2020',
							},
							{
								user_name: 'Jenny Wilson',
								user_id: 5043,
								id: 11,
								mobile: 9876543121,
								email: 'diannerussell@email.com',
								role_access: ['Role 1'],
								policy: ['Policy 1'],
								last_login_date_joined: '21 Sep, 2020',
							},
							{
								user_name: 'Jenny Wilson',
								user_id: 5043,
								id: 11,
								mobile: 9876543121,
								email: 'diannerussell@email.com',
								role_access: ['Role 1'],
								policy: ['Policy 1'],
								last_login_date_joined: '21 Sep, 2020',
							},
							{
								user_name: 'Jenny Wilson',
								user_id: 5043,
								id: 11,
								mobile: 9876543121,
								email: 'diannerussell@email.com',
								role_access: ['Role 1'],
								policy: ['Policy 1'],
								last_login_date_joined: '21 Sep, 2020',
							},
							{
								user_name: 'Jenny Wilson',
								user_id: 5043,
								id: 11,
								mobile: 9876543121,
								email: 'diannerussell@email.com',
								role_access: ['Role 1'],
								policy: ['Policy 1'],
								last_login_date_joined: '21 Sep, 2020',
							},
							{
								user_name: 'Jenny Wilson',
								user_id: 5043,
								id: 11,
								mobile: 9876543121,
								email: 'diannerussell@email.com',
								role_access: ['Role 1'],
								policy: ['Policy 1'],
								last_login_date_joined: '21 Sep, 2020',
							},
							{
								user_name: 'Jenny Wilson',
								user_id: 5043,
								id: 11,
								mobile: 9876543121,
								email: 'diannerussell@email.com',
								role_access: ['Role 1'],
								policy: ['Policy 1'],
								last_login_date_joined: '21 Sep, 2020',
							},
							{
								user_name: 'Jenny Wilson',
								user_id: 5043,
								id: 11,
								mobile: 9876543121,
								email: 'diannerussell@email.com',
								role_access: ['Role 1'],
								policy: ['Policy 1'],
								last_login_date_joined: '21 Sep, 2020',
							},
							{
								user_name: 'Jenny Wilson',
								user_id: 5043,
								id: 11,
								mobile: 9876543121,
								email: 'diannerussell@email.com',
								role_access: ['Role 1'],
								policy: ['Policy 1'],
								last_login_date_joined: '21 Sep, 2020',
							},
							{
								user_name: 'Jenny Wilson',
								user_id: 5043,
								id: 11,
								mobile: 9876543121,
								email: 'diannerussell@email.com',
								role_access: ['Role 1'],
								policy: ['Policy 1'],
								last_login_date_joined: '21 Sep, 2020',
							},
							{
								user_name: 'Jenny Wilson',
								user_id: 5043,
								id: 11,
								mobile: 9876543121,
								email: 'diannerussell@email.com',
								role_access: ['Role 1'],
								policy: ['Policy 1'],
								last_login_date_joined: '21 Sep, 2020',
							},
							{
								user_name: 'Jenny Wilson',
								user_id: 5043,
								id: 11,
								mobile: 9876543121,
								email: 'diannerussell@email.com',
								role_access: ['Role 1'],
								policy: ['Policy 1'],
								last_login_date_joined: '21 Sep, 2020',
							},
							{
								user_name: 'Jenny Wilson',
								user_id: 5043,
								id: 11,
								mobile: 9876543121,
								email: 'diannerussell@email.com',
								role_access: ['Role 1'],
								policy: ['Policy 1'],
								last_login_date_joined: '21 Sep, 2020',
							},
							{
								user_name: 'Jenny Wilson',
								user_id: 5043,
								id: 11,
								mobile: 9876543121,
								email: 'diannerussell@email.com',
								role_access: ['Role 1'],
								policy: ['Policy 1'],
								last_login_date_joined: '21 Sep, 2020',
							},
							{
								user_name: 'Jenny Wilson',
								user_id: 5043,
								id: 11,
								mobile: 9876543121,
								email: 'diannerussell@email.com',
								role_access: ['Role 1'],
								policy: ['Policy 1'],
								last_login_date_joined: '21 Sep, 2020',
							},
						]}
					/>
				</div>
			</div>
			<AddNewUserModal />
		</>
	);
}
