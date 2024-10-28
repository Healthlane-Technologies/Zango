import { rest } from 'msw';

export const appConfigurationHandlers = [
	rest.get('/api/v1/apps/:appId', (req, res, ctx) => {
		return res(
			ctx.delay(500),
			ctx.status(200),
			ctx.json({
				success: true,
				response: {
					app: {
						id: 20,
						schema_name: 'zapp1',
						created_at: '2023-08-31T11:03:00.079548Z',
						created_by: '',
						modified_at: '2023-08-31T11:03:01.090709Z',
						modified_by: '',
						uuid: '02248bb4-e120-48fa-bb64-a1c6ee032cb5',
						name: 'zapp1',
						description: `Lorem Ipsum is simply dummy text of th\ne printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently \n with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum.`,
						tenant_type: 'app',
						status: 'deployed',
						deployed_on: null,
						suspended_on: null,
						deleted_on: null,
						timezone: 'Asia/Kolkata',
						language: null,
						date_format: null,
						datetime_format: '%d/%m/%y %I:%M %p',
						datetime_format_display: 'August 05 2006, 3:05 PM',
						logo: '',
						fav_icon: '',
						extra_config: {"git_config":{"branch":{"dev":"dev","prod":"main","staging":"staging"},"repo_url":"https://github.com/Healthlane-Technologies/Zango"},"sync_packages":true},
						domains: [
							{ domain: 'zel3-neapp.zelthy.in', is_primary: true },
							{ domain: 'domainame2.com', is_primary: false },
							{ domain: 'domainame3.com', is_primary: false },
						],
					},
					dropdown_options: {
						timezones: [
							{
								id: 'Africa/Abidjan',
								label: 'Africa/Abidjan',
							},
							{
								id: 'Africa/Accra',
								label: 'Africa/Accra',
							},
							{
								id: 'Africa/Addis_Ababa',
								label: 'Africa/Addis_Ababa',
							},
							{
								id: 'Africa/Algiers',
								label: 'Africa/Algiers',
							},
							{
								id: 'Africa/Asmara',
								label: 'Africa/Asmara',
							},
							{
								id: 'Africa/Asmera',
								label: 'Africa/Asmera',
							},
							{
								id: 'Africa/Bamako',
								label: 'Africa/Bamako',
							},
							{
								id: 'Africa/Bangui',
								label: 'Africa/Bangui',
							},
							{
								id: 'Africa/Banjul',
								label: 'Africa/Banjul',
							},
							{
								id: 'Africa/Bissau',
								label: 'Africa/Bissau',
							},
							{
								id: 'Africa/Blantyre',
								label: 'Africa/Blantyre',
							},
							{
								id: 'Africa/Brazzaville',
								label: 'Africa/Brazzaville',
							},
							{
								id: 'Africa/Bujumbura',
								label: 'Africa/Bujumbura',
							},
							{
								id: 'Africa/Cairo',
								label: 'Africa/Cairo',
							},
							{
								id: 'Africa/Casablanca',
								label: 'Africa/Casablanca',
							},
							{
								id: 'Africa/Ceuta',
								label: 'Africa/Ceuta',
							},
							{
								id: 'Africa/Conakry',
								label: 'Africa/Conakry',
							},
							{
								id: 'Africa/Dakar',
								label: 'Africa/Dakar',
							},
							{
								id: 'Africa/Dar_es_Salaam',
								label: 'Africa/Dar_es_Salaam',
							},
							{
								id: 'Africa/Djibouti',
								label: 'Africa/Djibouti',
							},
							{
								id: 'Africa/Douala',
								label: 'Africa/Douala',
							},
							{
								id: 'Africa/El_Aaiun',
								label: 'Africa/El_Aaiun',
							},
							{
								id: 'Africa/Freetown',
								label: 'Africa/Freetown',
							},
							{
								id: 'Africa/Gaborone',
								label: 'Africa/Gaborone',
							},
							{
								id: 'Africa/Harare',
								label: 'Africa/Harare',
							},
							{
								id: 'Africa/Johannesburg',
								label: 'Africa/Johannesburg',
							},
							{
								id: 'Africa/Juba',
								label: 'Africa/Juba',
							},
							{
								id: 'Africa/Kampala',
								label: 'Africa/Kampala',
							},
							{
								id: 'Africa/Khartoum',
								label: 'Africa/Khartoum',
							},
							{
								id: 'Africa/Kigali',
								label: 'Africa/Kigali',
							},
							{
								id: 'Africa/Kinshasa',
								label: 'Africa/Kinshasa',
							},
							{
								id: 'Africa/Lagos',
								label: 'Africa/Lagos',
							},
							{
								id: 'Africa/Libreville',
								label: 'Africa/Libreville',
							},
							{
								id: 'Africa/Lome',
								label: 'Africa/Lome',
							},
							{
								id: 'Africa/Luanda',
								label: 'Africa/Luanda',
							},
							{
								id: 'Africa/Lubumbashi',
								label: 'Africa/Lubumbashi',
							},
							{
								id: 'Africa/Lusaka',
								label: 'Africa/Lusaka',
							},
							{
								id: 'Africa/Malabo',
								label: 'Africa/Malabo',
							},
							{
								id: 'Africa/Maputo',
								label: 'Africa/Maputo',
							},
							{
								id: 'Africa/Maseru',
								label: 'Africa/Maseru',
							},
							{
								id: 'Africa/Mbabane',
								label: 'Africa/Mbabane',
							},
							{
								id: 'Africa/Mogadishu',
								label: 'Africa/Mogadishu',
							},
							{
								id: 'Africa/Monrovia',
								label: 'Africa/Monrovia',
							},
							{
								id: 'Africa/Nairobi',
								label: 'Africa/Nairobi',
							},
							{
								id: 'Africa/Ndjamena',
								label: 'Africa/Ndjamena',
							},
							{
								id: 'Africa/Niamey',
								label: 'Africa/Niamey',
							},
							{
								id: 'Africa/Nouakchott',
								label: 'Africa/Nouakchott',
							},
							{
								id: 'Africa/Ouagadougou',
								label: 'Africa/Ouagadougou',
							},
							{
								id: 'Africa/Porto-Novo',
								label: 'Africa/Porto-Novo',
							},
							{
								id: 'Africa/Sao_Tome',
								label: 'Africa/Sao_Tome',
							},
							{
								id: 'Africa/Timbuktu',
								label: 'Africa/Timbuktu',
							},
							{
								id: 'Africa/Tripoli',
								label: 'Africa/Tripoli',
							},
							{
								id: 'Africa/Tunis',
								label: 'Africa/Tunis',
							},
							{
								id: 'Africa/Windhoek',
								label: 'Africa/Windhoek',
							},
							{
								id: 'America/Adak',
								label: 'America/Adak',
							},
							{
								id: 'America/Anchorage',
								label: 'America/Anchorage',
							},
							{
								id: 'America/Anguilla',
								label: 'America/Anguilla',
							},
							{
								id: 'America/Antigua',
								label: 'America/Antigua',
							},
							{
								id: 'America/Araguaina',
								label: 'America/Araguaina',
							},
							{
								id: 'America/Argentina/Buenos_Aires',
								label: 'America/Argentina/Buenos_Aires',
							},
							{
								id: 'America/Argentina/Catamarca',
								label: 'America/Argentina/Catamarca',
							},
							{
								id: 'America/Argentina/ComodRivadavia',
								label: 'America/Argentina/ComodRivadavia',
							},
							{
								id: 'America/Argentina/Cordoba',
								label: 'America/Argentina/Cordoba',
							},
							{
								id: 'America/Argentina/Jujuy',
								label: 'America/Argentina/Jujuy',
							},
							{
								id: 'America/Argentina/La_Rioja',
								label: 'America/Argentina/La_Rioja',
							},
							{
								id: 'America/Argentina/Mendoza',
								label: 'America/Argentina/Mendoza',
							},
							{
								id: 'America/Argentina/Rio_Gallegos',
								label: 'America/Argentina/Rio_Gallegos',
							},
							{
								id: 'America/Argentina/Salta',
								label: 'America/Argentina/Salta',
							},
							{
								id: 'America/Argentina/San_Juan',
								label: 'America/Argentina/San_Juan',
							},
							{
								id: 'America/Argentina/San_Luis',
								label: 'America/Argentina/San_Luis',
							},
							{
								id: 'America/Argentina/Tucuman',
								label: 'America/Argentina/Tucuman',
							},
							{
								id: 'America/Argentina/Ushuaia',
								label: 'America/Argentina/Ushuaia',
							},
							{
								id: 'America/Aruba',
								label: 'America/Aruba',
							},
							{
								id: 'America/Asuncion',
								label: 'America/Asuncion',
							},
							{
								id: 'America/Atikokan',
								label: 'America/Atikokan',
							},
							{
								id: 'America/Atka',
								label: 'America/Atka',
							},
							{
								id: 'America/Bahia',
								label: 'America/Bahia',
							},
							{
								id: 'America/Bahia_Banderas',
								label: 'America/Bahia_Banderas',
							},
							{
								id: 'America/Barbados',
								label: 'America/Barbados',
							},
							{
								id: 'America/Belem',
								label: 'America/Belem',
							},
							{
								id: 'America/Belize',
								label: 'America/Belize',
							},
							{
								id: 'America/Blanc-Sablon',
								label: 'America/Blanc-Sablon',
							},
							{
								id: 'America/Boa_Vista',
								label: 'America/Boa_Vista',
							},
							{
								id: 'America/Bogota',
								label: 'America/Bogota',
							},
							{
								id: 'America/Boise',
								label: 'America/Boise',
							},
							{
								id: 'America/Buenos_Aires',
								label: 'America/Buenos_Aires',
							},
							{
								id: 'America/Cambridge_Bay',
								label: 'America/Cambridge_Bay',
							},
							{
								id: 'America/Campo_Grande',
								label: 'America/Campo_Grande',
							},
							{
								id: 'America/Cancun',
								label: 'America/Cancun',
							},
							{
								id: 'America/Caracas',
								label: 'America/Caracas',
							},
							{
								id: 'America/Catamarca',
								label: 'America/Catamarca',
							},
							{
								id: 'America/Cayenne',
								label: 'America/Cayenne',
							},
							{
								id: 'America/Cayman',
								label: 'America/Cayman',
							},
							{
								id: 'America/Chicago',
								label: 'America/Chicago',
							},
							{
								id: 'America/Chihuahua',
								label: 'America/Chihuahua',
							},
							{
								id: 'America/Ciudad_Juarez',
								label: 'America/Ciudad_Juarez',
							},
							{
								id: 'America/Coral_Harbour',
								label: 'America/Coral_Harbour',
							},
							{
								id: 'America/Cordoba',
								label: 'America/Cordoba',
							},
							{
								id: 'America/Costa_Rica',
								label: 'America/Costa_Rica',
							},
							{
								id: 'America/Creston',
								label: 'America/Creston',
							},
							{
								id: 'America/Cuiaba',
								label: 'America/Cuiaba',
							},
							{
								id: 'America/Curacao',
								label: 'America/Curacao',
							},
							{
								id: 'America/Danmarkshavn',
								label: 'America/Danmarkshavn',
							},
							{
								id: 'America/Dawson',
								label: 'America/Dawson',
							},
							{
								id: 'America/Dawson_Creek',
								label: 'America/Dawson_Creek',
							},
							{
								id: 'America/Denver',
								label: 'America/Denver',
							},
							{
								id: 'America/Detroit',
								label: 'America/Detroit',
							},
							{
								id: 'America/Dominica',
								label: 'America/Dominica',
							},
							{
								id: 'America/Edmonton',
								label: 'America/Edmonton',
							},
							{
								id: 'America/Eirunepe',
								label: 'America/Eirunepe',
							},
							{
								id: 'America/El_Salvador',
								label: 'America/El_Salvador',
							},
							{
								id: 'America/Ensenada',
								label: 'America/Ensenada',
							},
							{
								id: 'America/Fort_Nelson',
								label: 'America/Fort_Nelson',
							},
							{
								id: 'America/Fort_Wayne',
								label: 'America/Fort_Wayne',
							},
							{
								id: 'America/Fortaleza',
								label: 'America/Fortaleza',
							},
							{
								id: 'America/Glace_Bay',
								label: 'America/Glace_Bay',
							},
							{
								id: 'America/Godthab',
								label: 'America/Godthab',
							},
							{
								id: 'America/Goose_Bay',
								label: 'America/Goose_Bay',
							},
							{
								id: 'America/Grand_Turk',
								label: 'America/Grand_Turk',
							},
							{
								id: 'America/Grenada',
								label: 'America/Grenada',
							},
							{
								id: 'America/Guadeloupe',
								label: 'America/Guadeloupe',
							},
							{
								id: 'America/Guatemala',
								label: 'America/Guatemala',
							},
							{
								id: 'America/Guayaquil',
								label: 'America/Guayaquil',
							},
							{
								id: 'America/Guyana',
								label: 'America/Guyana',
							},
							{
								id: 'America/Halifax',
								label: 'America/Halifax',
							},
							{
								id: 'America/Havana',
								label: 'America/Havana',
							},
							{
								id: 'America/Hermosillo',
								label: 'America/Hermosillo',
							},
							{
								id: 'America/Indiana/Indianapolis',
								label: 'America/Indiana/Indianapolis',
							},
							{
								id: 'America/Indiana/Knox',
								label: 'America/Indiana/Knox',
							},
							{
								id: 'America/Indiana/Marengo',
								label: 'America/Indiana/Marengo',
							},
							{
								id: 'America/Indiana/Petersburg',
								label: 'America/Indiana/Petersburg',
							},
							{
								id: 'America/Indiana/Tell_City',
								label: 'America/Indiana/Tell_City',
							},
							{
								id: 'America/Indiana/Vevay',
								label: 'America/Indiana/Vevay',
							},
							{
								id: 'America/Indiana/Vincennes',
								label: 'America/Indiana/Vincennes',
							},
							{
								id: 'America/Indiana/Winamac',
								label: 'America/Indiana/Winamac',
							},
							{
								id: 'America/Indianapolis',
								label: 'America/Indianapolis',
							},
							{
								id: 'America/Inuvik',
								label: 'America/Inuvik',
							},
							{
								id: 'America/Iqaluit',
								label: 'America/Iqaluit',
							},
							{
								id: 'America/Jamaica',
								label: 'America/Jamaica',
							},
							{
								id: 'America/Jujuy',
								label: 'America/Jujuy',
							},
							{
								id: 'America/Juneau',
								label: 'America/Juneau',
							},
							{
								id: 'America/Kentucky/Louisville',
								label: 'America/Kentucky/Louisville',
							},
							{
								id: 'America/Kentucky/Monticello',
								label: 'America/Kentucky/Monticello',
							},
							{
								id: 'America/Knox_IN',
								label: 'America/Knox_IN',
							},
							{
								id: 'America/Kralendijk',
								label: 'America/Kralendijk',
							},
							{
								id: 'America/La_Paz',
								label: 'America/La_Paz',
							},
							{
								id: 'America/Lima',
								label: 'America/Lima',
							},
							{
								id: 'America/Los_Angeles',
								label: 'America/Los_Angeles',
							},
							{
								id: 'America/Louisville',
								label: 'America/Louisville',
							},
							{
								id: 'America/Lower_Princes',
								label: 'America/Lower_Princes',
							},
							{
								id: 'America/Maceio',
								label: 'America/Maceio',
							},
							{
								id: 'America/Managua',
								label: 'America/Managua',
							},
							{
								id: 'America/Manaus',
								label: 'America/Manaus',
							},
							{
								id: 'America/Marigot',
								label: 'America/Marigot',
							},
							{
								id: 'America/Martinique',
								label: 'America/Martinique',
							},
							{
								id: 'America/Matamoros',
								label: 'America/Matamoros',
							},
							{
								id: 'America/Mazatlan',
								label: 'America/Mazatlan',
							},
							{
								id: 'America/Mendoza',
								label: 'America/Mendoza',
							},
							{
								id: 'America/Menominee',
								label: 'America/Menominee',
							},
							{
								id: 'America/Merida',
								label: 'America/Merida',
							},
							{
								id: 'America/Metlakatla',
								label: 'America/Metlakatla',
							},
							{
								id: 'America/Mexico_City',
								label: 'America/Mexico_City',
							},
							{
								id: 'America/Miquelon',
								label: 'America/Miquelon',
							},
							{
								id: 'America/Moncton',
								label: 'America/Moncton',
							},
							{
								id: 'America/Monterrey',
								label: 'America/Monterrey',
							},
							{
								id: 'America/Montevideo',
								label: 'America/Montevideo',
							},
							{
								id: 'America/Montreal',
								label: 'America/Montreal',
							},
							{
								id: 'America/Montserrat',
								label: 'America/Montserrat',
							},
							{
								id: 'America/Nassau',
								label: 'America/Nassau',
							},
							{
								id: 'America/New_York',
								label: 'America/New_York',
							},
							{
								id: 'America/Nipigon',
								label: 'America/Nipigon',
							},
							{
								id: 'America/Nome',
								label: 'America/Nome',
							},
							{
								id: 'America/Noronha',
								label: 'America/Noronha',
							},
							{
								id: 'America/North_Dakota/Beulah',
								label: 'America/North_Dakota/Beulah',
							},
							{
								id: 'America/North_Dakota/Center',
								label: 'America/North_Dakota/Center',
							},
							{
								id: 'America/North_Dakota/New_Salem',
								label: 'America/North_Dakota/New_Salem',
							},
							{
								id: 'America/Nuuk',
								label: 'America/Nuuk',
							},
							{
								id: 'America/Ojinaga',
								label: 'America/Ojinaga',
							},
							{
								id: 'America/Panama',
								label: 'America/Panama',
							},
							{
								id: 'America/Pangnirtung',
								label: 'America/Pangnirtung',
							},
							{
								id: 'America/Paramaribo',
								label: 'America/Paramaribo',
							},
							{
								id: 'America/Phoenix',
								label: 'America/Phoenix',
							},
							{
								id: 'America/Port-au-Prince',
								label: 'America/Port-au-Prince',
							},
							{
								id: 'America/Port_of_Spain',
								label: 'America/Port_of_Spain',
							},
							{
								id: 'America/Porto_Acre',
								label: 'America/Porto_Acre',
							},
							{
								id: 'America/Porto_Velho',
								label: 'America/Porto_Velho',
							},
							{
								id: 'America/Puerto_Rico',
								label: 'America/Puerto_Rico',
							},
							{
								id: 'America/Punta_Arenas',
								label: 'America/Punta_Arenas',
							},
							{
								id: 'America/Rainy_River',
								label: 'America/Rainy_River',
							},
							{
								id: 'America/Rankin_Inlet',
								label: 'America/Rankin_Inlet',
							},
							{
								id: 'America/Recife',
								label: 'America/Recife',
							},
							{
								id: 'America/Regina',
								label: 'America/Regina',
							},
							{
								id: 'America/Resolute',
								label: 'America/Resolute',
							},
							{
								id: 'America/Rio_Branco',
								label: 'America/Rio_Branco',
							},
							{
								id: 'America/Rosario',
								label: 'America/Rosario',
							},
							{
								id: 'America/Santa_Isabel',
								label: 'America/Santa_Isabel',
							},
							{
								id: 'America/Santarem',
								label: 'America/Santarem',
							},
							{
								id: 'America/Santiago',
								label: 'America/Santiago',
							},
							{
								id: 'America/Santo_Domingo',
								label: 'America/Santo_Domingo',
							},
							{
								id: 'America/Sao_Paulo',
								label: 'America/Sao_Paulo',
							},
							{
								id: 'America/Scoresbysund',
								label: 'America/Scoresbysund',
							},
							{
								id: 'America/Shiprock',
								label: 'America/Shiprock',
							},
							{
								id: 'America/Sitka',
								label: 'America/Sitka',
							},
							{
								id: 'America/St_Barthelemy',
								label: 'America/St_Barthelemy',
							},
							{
								id: 'America/St_Johns',
								label: 'America/St_Johns',
							},
							{
								id: 'America/St_Kitts',
								label: 'America/St_Kitts',
							},
							{
								id: 'America/St_Lucia',
								label: 'America/St_Lucia',
							},
							{
								id: 'America/St_Thomas',
								label: 'America/St_Thomas',
							},
							{
								id: 'America/St_Vincent',
								label: 'America/St_Vincent',
							},
							{
								id: 'America/Swift_Current',
								label: 'America/Swift_Current',
							},
							{
								id: 'America/Tegucigalpa',
								label: 'America/Tegucigalpa',
							},
							{
								id: 'America/Thule',
								label: 'America/Thule',
							},
							{
								id: 'America/Thunder_Bay',
								label: 'America/Thunder_Bay',
							},
							{
								id: 'America/Tijuana',
								label: 'America/Tijuana',
							},
							{
								id: 'America/Toronto',
								label: 'America/Toronto',
							},
							{
								id: 'America/Tortola',
								label: 'America/Tortola',
							},
							{
								id: 'America/Vancouver',
								label: 'America/Vancouver',
							},
							{
								id: 'America/Virgin',
								label: 'America/Virgin',
							},
							{
								id: 'America/Whitehorse',
								label: 'America/Whitehorse',
							},
							{
								id: 'America/Winnipeg',
								label: 'America/Winnipeg',
							},
							{
								id: 'America/Yakutat',
								label: 'America/Yakutat',
							},
							{
								id: 'America/Yellowknife',
								label: 'America/Yellowknife',
							},
							{
								id: 'Antarctica/Casey',
								label: 'Antarctica/Casey',
							},
							{
								id: 'Antarctica/Davis',
								label: 'Antarctica/Davis',
							},
							{
								id: 'Antarctica/DumontDUrville',
								label: 'Antarctica/DumontDUrville',
							},
							{
								id: 'Antarctica/Macquarie',
								label: 'Antarctica/Macquarie',
							},
							{
								id: 'Antarctica/Mawson',
								label: 'Antarctica/Mawson',
							},
							{
								id: 'Antarctica/McMurdo',
								label: 'Antarctica/McMurdo',
							},
							{
								id: 'Antarctica/Palmer',
								label: 'Antarctica/Palmer',
							},
							{
								id: 'Antarctica/Rothera',
								label: 'Antarctica/Rothera',
							},
							{
								id: 'Antarctica/South_Pole',
								label: 'Antarctica/South_Pole',
							},
							{
								id: 'Antarctica/Syowa',
								label: 'Antarctica/Syowa',
							},
							{
								id: 'Antarctica/Troll',
								label: 'Antarctica/Troll',
							},
							{
								id: 'Antarctica/Vostok',
								label: 'Antarctica/Vostok',
							},
							{
								id: 'Arctic/Longyearbyen',
								label: 'Arctic/Longyearbyen',
							},
							{
								id: 'Asia/Aden',
								label: 'Asia/Aden',
							},
							{
								id: 'Asia/Almaty',
								label: 'Asia/Almaty',
							},
							{
								id: 'Asia/Amman',
								label: 'Asia/Amman',
							},
							{
								id: 'Asia/Anadyr',
								label: 'Asia/Anadyr',
							},
							{
								id: 'Asia/Aqtau',
								label: 'Asia/Aqtau',
							},
							{
								id: 'Asia/Aqtobe',
								label: 'Asia/Aqtobe',
							},
							{
								id: 'Asia/Ashgabat',
								label: 'Asia/Ashgabat',
							},
							{
								id: 'Asia/Ashkhabad',
								label: 'Asia/Ashkhabad',
							},
							{
								id: 'Asia/Atyrau',
								label: 'Asia/Atyrau',
							},
							{
								id: 'Asia/Baghdad',
								label: 'Asia/Baghdad',
							},
							{
								id: 'Asia/Bahrain',
								label: 'Asia/Bahrain',
							},
							{
								id: 'Asia/Baku',
								label: 'Asia/Baku',
							},
							{
								id: 'Asia/Bangkok',
								label: 'Asia/Bangkok',
							},
							{
								id: 'Asia/Barnaul',
								label: 'Asia/Barnaul',
							},
							{
								id: 'Asia/Beirut',
								label: 'Asia/Beirut',
							},
							{
								id: 'Asia/Bishkek',
								label: 'Asia/Bishkek',
							},
							{
								id: 'Asia/Brunei',
								label: 'Asia/Brunei',
							},
							{
								id: 'Asia/Calcutta',
								label: 'Asia/Calcutta',
							},
							{
								id: 'Asia/Chita',
								label: 'Asia/Chita',
							},
							{
								id: 'Asia/Choibalsan',
								label: 'Asia/Choibalsan',
							},
							{
								id: 'Asia/Chongqing',
								label: 'Asia/Chongqing',
							},
							{
								id: 'Asia/Chungking',
								label: 'Asia/Chungking',
							},
							{
								id: 'Asia/Colombo',
								label: 'Asia/Colombo',
							},
							{
								id: 'Asia/Dacca',
								label: 'Asia/Dacca',
							},
							{
								id: 'Asia/Damascus',
								label: 'Asia/Damascus',
							},
							{
								id: 'Asia/Dhaka',
								label: 'Asia/Dhaka',
							},
							{
								id: 'Asia/Dili',
								label: 'Asia/Dili',
							},
							{
								id: 'Asia/Dubai',
								label: 'Asia/Dubai',
							},
							{
								id: 'Asia/Dushanbe',
								label: 'Asia/Dushanbe',
							},
							{
								id: 'Asia/Famagusta',
								label: 'Asia/Famagusta',
							},
							{
								id: 'Asia/Gaza',
								label: 'Asia/Gaza',
							},
							{
								id: 'Asia/Harbin',
								label: 'Asia/Harbin',
							},
							{
								id: 'Asia/Hebron',
								label: 'Asia/Hebron',
							},
							{
								id: 'Asia/Ho_Chi_Minh',
								label: 'Asia/Ho_Chi_Minh',
							},
							{
								id: 'Asia/Hong_Kong',
								label: 'Asia/Hong_Kong',
							},
							{
								id: 'Asia/Hovd',
								label: 'Asia/Hovd',
							},
							{
								id: 'Asia/Irkutsk',
								label: 'Asia/Irkutsk',
							},
							{
								id: 'Asia/Istanbul',
								label: 'Asia/Istanbul',
							},
							{
								id: 'Asia/Jakarta',
								label: 'Asia/Jakarta',
							},
							{
								id: 'Asia/Jayapura',
								label: 'Asia/Jayapura',
							},
							{
								id: 'Asia/Jerusalem',
								label: 'Asia/Jerusalem',
							},
							{
								id: 'Asia/Kabul',
								label: 'Asia/Kabul',
							},
							{
								id: 'Asia/Kamchatka',
								label: 'Asia/Kamchatka',
							},
							{
								id: 'Asia/Karachi',
								label: 'Asia/Karachi',
							},
							{
								id: 'Asia/Kashgar',
								label: 'Asia/Kashgar',
							},
							{
								id: 'Asia/Kathmandu',
								label: 'Asia/Kathmandu',
							},
							{
								id: 'Asia/Katmandu',
								label: 'Asia/Katmandu',
							},
							{
								id: 'Asia/Khandyga',
								label: 'Asia/Khandyga',
							},
							{
								id: 'Asia/Kolkata',
								label: 'Asia/Kolkata',
							},
							{
								id: 'Asia/Krasnoyarsk',
								label: 'Asia/Krasnoyarsk',
							},
							{
								id: 'Asia/Kuala_Lumpur',
								label: 'Asia/Kuala_Lumpur',
							},
							{
								id: 'Asia/Kuching',
								label: 'Asia/Kuching',
							},
							{
								id: 'Asia/Kuwait',
								label: 'Asia/Kuwait',
							},
							{
								id: 'Asia/Macao',
								label: 'Asia/Macao',
							},
							{
								id: 'Asia/Macau',
								label: 'Asia/Macau',
							},
							{
								id: 'Asia/Magadan',
								label: 'Asia/Magadan',
							},
							{
								id: 'Asia/Makassar',
								label: 'Asia/Makassar',
							},
							{
								id: 'Asia/Manila',
								label: 'Asia/Manila',
							},
							{
								id: 'Asia/Muscat',
								label: 'Asia/Muscat',
							},
							{
								id: 'Asia/Nicosia',
								label: 'Asia/Nicosia',
							},
							{
								id: 'Asia/Novokuznetsk',
								label: 'Asia/Novokuznetsk',
							},
							{
								id: 'Asia/Novosibirsk',
								label: 'Asia/Novosibirsk',
							},
							{
								id: 'Asia/Omsk',
								label: 'Asia/Omsk',
							},
							{
								id: 'Asia/Oral',
								label: 'Asia/Oral',
							},
							{
								id: 'Asia/Phnom_Penh',
								label: 'Asia/Phnom_Penh',
							},
							{
								id: 'Asia/Pontianak',
								label: 'Asia/Pontianak',
							},
							{
								id: 'Asia/Pyongyang',
								label: 'Asia/Pyongyang',
							},
							{
								id: 'Asia/Qatar',
								label: 'Asia/Qatar',
							},
							{
								id: 'Asia/Qostanay',
								label: 'Asia/Qostanay',
							},
							{
								id: 'Asia/Qyzylorda',
								label: 'Asia/Qyzylorda',
							},
							{
								id: 'Asia/Rangoon',
								label: 'Asia/Rangoon',
							},
							{
								id: 'Asia/Riyadh',
								label: 'Asia/Riyadh',
							},
							{
								id: 'Asia/Saigon',
								label: 'Asia/Saigon',
							},
							{
								id: 'Asia/Sakhalin',
								label: 'Asia/Sakhalin',
							},
							{
								id: 'Asia/Samarkand',
								label: 'Asia/Samarkand',
							},
							{
								id: 'Asia/Seoul',
								label: 'Asia/Seoul',
							},
							{
								id: 'Asia/Shanghai',
								label: 'Asia/Shanghai',
							},
							{
								id: 'Asia/Singapore',
								label: 'Asia/Singapore',
							},
							{
								id: 'Asia/Srednekolymsk',
								label: 'Asia/Srednekolymsk',
							},
							{
								id: 'Asia/Taipei',
								label: 'Asia/Taipei',
							},
							{
								id: 'Asia/Tashkent',
								label: 'Asia/Tashkent',
							},
							{
								id: 'Asia/Tbilisi',
								label: 'Asia/Tbilisi',
							},
							{
								id: 'Asia/Tehran',
								label: 'Asia/Tehran',
							},
							{
								id: 'Asia/Tel_Aviv',
								label: 'Asia/Tel_Aviv',
							},
							{
								id: 'Asia/Thimbu',
								label: 'Asia/Thimbu',
							},
							{
								id: 'Asia/Thimphu',
								label: 'Asia/Thimphu',
							},
							{
								id: 'Asia/Tokyo',
								label: 'Asia/Tokyo',
							},
							{
								id: 'Asia/Tomsk',
								label: 'Asia/Tomsk',
							},
							{
								id: 'Asia/Ujung_Pandang',
								label: 'Asia/Ujung_Pandang',
							},
							{
								id: 'Asia/Ulaanbaatar',
								label: 'Asia/Ulaanbaatar',
							},
							{
								id: 'Asia/Ulan_Bator',
								label: 'Asia/Ulan_Bator',
							},
							{
								id: 'Asia/Urumqi',
								label: 'Asia/Urumqi',
							},
							{
								id: 'Asia/Ust-Nera',
								label: 'Asia/Ust-Nera',
							},
							{
								id: 'Asia/Vientiane',
								label: 'Asia/Vientiane',
							},
							{
								id: 'Asia/Vladivostok',
								label: 'Asia/Vladivostok',
							},
							{
								id: 'Asia/Yakutsk',
								label: 'Asia/Yakutsk',
							},
							{
								id: 'Asia/Yangon',
								label: 'Asia/Yangon',
							},
							{
								id: 'Asia/Yekaterinburg',
								label: 'Asia/Yekaterinburg',
							},
							{
								id: 'Asia/Yerevan',
								label: 'Asia/Yerevan',
							},
							{
								id: 'Atlantic/Azores',
								label: 'Atlantic/Azores',
							},
							{
								id: 'Atlantic/Bermuda',
								label: 'Atlantic/Bermuda',
							},
							{
								id: 'Atlantic/Canary',
								label: 'Atlantic/Canary',
							},
							{
								id: 'Atlantic/Cape_Verde',
								label: 'Atlantic/Cape_Verde',
							},
							{
								id: 'Atlantic/Faeroe',
								label: 'Atlantic/Faeroe',
							},
							{
								id: 'Atlantic/Faroe',
								label: 'Atlantic/Faroe',
							},
							{
								id: 'Atlantic/Jan_Mayen',
								label: 'Atlantic/Jan_Mayen',
							},
							{
								id: 'Atlantic/Madeira',
								label: 'Atlantic/Madeira',
							},
							{
								id: 'Atlantic/Reykjavik',
								label: 'Atlantic/Reykjavik',
							},
							{
								id: 'Atlantic/South_Georgia',
								label: 'Atlantic/South_Georgia',
							},
							{
								id: 'Atlantic/St_Helena',
								label: 'Atlantic/St_Helena',
							},
							{
								id: 'Atlantic/Stanley',
								label: 'Atlantic/Stanley',
							},
							{
								id: 'Australia/ACT',
								label: 'Australia/ACT',
							},
							{
								id: 'Australia/Adelaide',
								label: 'Australia/Adelaide',
							},
							{
								id: 'Australia/Brisbane',
								label: 'Australia/Brisbane',
							},
							{
								id: 'Australia/Broken_Hill',
								label: 'Australia/Broken_Hill',
							},
							{
								id: 'Australia/Canberra',
								label: 'Australia/Canberra',
							},
							{
								id: 'Australia/Currie',
								label: 'Australia/Currie',
							},
							{
								id: 'Australia/Darwin',
								label: 'Australia/Darwin',
							},
							{
								id: 'Australia/Eucla',
								label: 'Australia/Eucla',
							},
							{
								id: 'Australia/Hobart',
								label: 'Australia/Hobart',
							},
							{
								id: 'Australia/LHI',
								label: 'Australia/LHI',
							},
							{
								id: 'Australia/Lindeman',
								label: 'Australia/Lindeman',
							},
							{
								id: 'Australia/Lord_Howe',
								label: 'Australia/Lord_Howe',
							},
							{
								id: 'Australia/Melbourne',
								label: 'Australia/Melbourne',
							},
							{
								id: 'Australia/NSW',
								label: 'Australia/NSW',
							},
							{
								id: 'Australia/North',
								label: 'Australia/North',
							},
							{
								id: 'Australia/Perth',
								label: 'Australia/Perth',
							},
							{
								id: 'Australia/Queensland',
								label: 'Australia/Queensland',
							},
							{
								id: 'Australia/South',
								label: 'Australia/South',
							},
							{
								id: 'Australia/Sydney',
								label: 'Australia/Sydney',
							},
							{
								id: 'Australia/Tasmania',
								label: 'Australia/Tasmania',
							},
							{
								id: 'Australia/Victoria',
								label: 'Australia/Victoria',
							},
							{
								id: 'Australia/West',
								label: 'Australia/West',
							},
							{
								id: 'Australia/Yancowinna',
								label: 'Australia/Yancowinna',
							},
							{
								id: 'Brazil/Acre',
								label: 'Brazil/Acre',
							},
							{
								id: 'Brazil/DeNoronha',
								label: 'Brazil/DeNoronha',
							},
							{
								id: 'Brazil/East',
								label: 'Brazil/East',
							},
							{
								id: 'Brazil/West',
								label: 'Brazil/West',
							},
							{
								id: 'CET',
								label: 'CET',
							},
							{
								id: 'CST6CDT',
								label: 'CST6CDT',
							},
							{
								id: 'Canada/Atlantic',
								label: 'Canada/Atlantic',
							},
							{
								id: 'Canada/Central',
								label: 'Canada/Central',
							},
							{
								id: 'Canada/Eastern',
								label: 'Canada/Eastern',
							},
							{
								id: 'Canada/Mountain',
								label: 'Canada/Mountain',
							},
							{
								id: 'Canada/Newfoundland',
								label: 'Canada/Newfoundland',
							},
							{
								id: 'Canada/Pacific',
								label: 'Canada/Pacific',
							},
							{
								id: 'Canada/Saskatchewan',
								label: 'Canada/Saskatchewan',
							},
							{
								id: 'Canada/Yukon',
								label: 'Canada/Yukon',
							},
							{
								id: 'Chile/Continental',
								label: 'Chile/Continental',
							},
							{
								id: 'Chile/EasterIsland',
								label: 'Chile/EasterIsland',
							},
							{
								id: 'Cuba',
								label: 'Cuba',
							},
							{
								id: 'EET',
								label: 'EET',
							},
							{
								id: 'EST',
								label: 'EST',
							},
							{
								id: 'EST5EDT',
								label: 'EST5EDT',
							},
							{
								id: 'Egypt',
								label: 'Egypt',
							},
							{
								id: 'Eire',
								label: 'Eire',
							},
							{
								id: 'Etc/GMT',
								label: 'Etc/GMT',
							},
							{
								id: 'Etc/GMT+0',
								label: 'Etc/GMT+0',
							},
							{
								id: 'Etc/GMT+1',
								label: 'Etc/GMT+1',
							},
							{
								id: 'Etc/GMT+10',
								label: 'Etc/GMT+10',
							},
							{
								id: 'Etc/GMT+11',
								label: 'Etc/GMT+11',
							},
							{
								id: 'Etc/GMT+12',
								label: 'Etc/GMT+12',
							},
							{
								id: 'Etc/GMT+2',
								label: 'Etc/GMT+2',
							},
							{
								id: 'Etc/GMT+3',
								label: 'Etc/GMT+3',
							},
							{
								id: 'Etc/GMT+4',
								label: 'Etc/GMT+4',
							},
							{
								id: 'Etc/GMT+5',
								label: 'Etc/GMT+5',
							},
							{
								id: 'Etc/GMT+6',
								label: 'Etc/GMT+6',
							},
							{
								id: 'Etc/GMT+7',
								label: 'Etc/GMT+7',
							},
							{
								id: 'Etc/GMT+8',
								label: 'Etc/GMT+8',
							},
							{
								id: 'Etc/GMT+9',
								label: 'Etc/GMT+9',
							},
							{
								id: 'Etc/GMT-0',
								label: 'Etc/GMT-0',
							},
							{
								id: 'Etc/GMT-1',
								label: 'Etc/GMT-1',
							},
							{
								id: 'Etc/GMT-10',
								label: 'Etc/GMT-10',
							},
							{
								id: 'Etc/GMT-11',
								label: 'Etc/GMT-11',
							},
							{
								id: 'Etc/GMT-12',
								label: 'Etc/GMT-12',
							},
							{
								id: 'Etc/GMT-13',
								label: 'Etc/GMT-13',
							},
							{
								id: 'Etc/GMT-14',
								label: 'Etc/GMT-14',
							},
							{
								id: 'Etc/GMT-2',
								label: 'Etc/GMT-2',
							},
							{
								id: 'Etc/GMT-3',
								label: 'Etc/GMT-3',
							},
							{
								id: 'Etc/GMT-4',
								label: 'Etc/GMT-4',
							},
							{
								id: 'Etc/GMT-5',
								label: 'Etc/GMT-5',
							},
							{
								id: 'Etc/GMT-6',
								label: 'Etc/GMT-6',
							},
							{
								id: 'Etc/GMT-7',
								label: 'Etc/GMT-7',
							},
							{
								id: 'Etc/GMT-8',
								label: 'Etc/GMT-8',
							},
							{
								id: 'Etc/GMT-9',
								label: 'Etc/GMT-9',
							},
							{
								id: 'Etc/GMT0',
								label: 'Etc/GMT0',
							},
							{
								id: 'Etc/Greenwich',
								label: 'Etc/Greenwich',
							},
							{
								id: 'Etc/UCT',
								label: 'Etc/UCT',
							},
							{
								id: 'Etc/UTC',
								label: 'Etc/UTC',
							},
							{
								id: 'Etc/Universal',
								label: 'Etc/Universal',
							},
							{
								id: 'Etc/Zulu',
								label: 'Etc/Zulu',
							},
							{
								id: 'Europe/Amsterdam',
								label: 'Europe/Amsterdam',
							},
							{
								id: 'Europe/Andorra',
								label: 'Europe/Andorra',
							},
							{
								id: 'Europe/Astrakhan',
								label: 'Europe/Astrakhan',
							},
							{
								id: 'Europe/Athens',
								label: 'Europe/Athens',
							},
							{
								id: 'Europe/Belfast',
								label: 'Europe/Belfast',
							},
							{
								id: 'Europe/Belgrade',
								label: 'Europe/Belgrade',
							},
							{
								id: 'Europe/Berlin',
								label: 'Europe/Berlin',
							},
							{
								id: 'Europe/Bratislava',
								label: 'Europe/Bratislava',
							},
							{
								id: 'Europe/Brussels',
								label: 'Europe/Brussels',
							},
							{
								id: 'Europe/Bucharest',
								label: 'Europe/Bucharest',
							},
							{
								id: 'Europe/Budapest',
								label: 'Europe/Budapest',
							},
							{
								id: 'Europe/Busingen',
								label: 'Europe/Busingen',
							},
							{
								id: 'Europe/Chisinau',
								label: 'Europe/Chisinau',
							},
							{
								id: 'Europe/Copenhagen',
								label: 'Europe/Copenhagen',
							},
							{
								id: 'Europe/Dublin',
								label: 'Europe/Dublin',
							},
							{
								id: 'Europe/Gibraltar',
								label: 'Europe/Gibraltar',
							},
							{
								id: 'Europe/Guernsey',
								label: 'Europe/Guernsey',
							},
							{
								id: 'Europe/Helsinki',
								label: 'Europe/Helsinki',
							},
							{
								id: 'Europe/Isle_of_Man',
								label: 'Europe/Isle_of_Man',
							},
							{
								id: 'Europe/Istanbul',
								label: 'Europe/Istanbul',
							},
							{
								id: 'Europe/Jersey',
								label: 'Europe/Jersey',
							},
							{
								id: 'Europe/Kaliningrad',
								label: 'Europe/Kaliningrad',
							},
							{
								id: 'Europe/Kiev',
								label: 'Europe/Kiev',
							},
							{
								id: 'Europe/Kirov',
								label: 'Europe/Kirov',
							},
							{
								id: 'Europe/Kyiv',
								label: 'Europe/Kyiv',
							},
							{
								id: 'Europe/Lisbon',
								label: 'Europe/Lisbon',
							},
							{
								id: 'Europe/Ljubljana',
								label: 'Europe/Ljubljana',
							},
							{
								id: 'Europe/London',
								label: 'Europe/London',
							},
							{
								id: 'Europe/Luxembourg',
								label: 'Europe/Luxembourg',
							},
							{
								id: 'Europe/Madrid',
								label: 'Europe/Madrid',
							},
							{
								id: 'Europe/Malta',
								label: 'Europe/Malta',
							},
							{
								id: 'Europe/Mariehamn',
								label: 'Europe/Mariehamn',
							},
							{
								id: 'Europe/Minsk',
								label: 'Europe/Minsk',
							},
							{
								id: 'Europe/Monaco',
								label: 'Europe/Monaco',
							},
							{
								id: 'Europe/Moscow',
								label: 'Europe/Moscow',
							},
							{
								id: 'Europe/Nicosia',
								label: 'Europe/Nicosia',
							},
							{
								id: 'Europe/Oslo',
								label: 'Europe/Oslo',
							},
							{
								id: 'Europe/Paris',
								label: 'Europe/Paris',
							},
							{
								id: 'Europe/Podgorica',
								label: 'Europe/Podgorica',
							},
							{
								id: 'Europe/Prague',
								label: 'Europe/Prague',
							},
							{
								id: 'Europe/Riga',
								label: 'Europe/Riga',
							},
							{
								id: 'Europe/Rome',
								label: 'Europe/Rome',
							},
							{
								id: 'Europe/Samara',
								label: 'Europe/Samara',
							},
							{
								id: 'Europe/San_Marino',
								label: 'Europe/San_Marino',
							},
							{
								id: 'Europe/Sarajevo',
								label: 'Europe/Sarajevo',
							},
							{
								id: 'Europe/Saratov',
								label: 'Europe/Saratov',
							},
							{
								id: 'Europe/Simferopol',
								label: 'Europe/Simferopol',
							},
							{
								id: 'Europe/Skopje',
								label: 'Europe/Skopje',
							},
							{
								id: 'Europe/Sofia',
								label: 'Europe/Sofia',
							},
							{
								id: 'Europe/Stockholm',
								label: 'Europe/Stockholm',
							},
							{
								id: 'Europe/Tallinn',
								label: 'Europe/Tallinn',
							},
							{
								id: 'Europe/Tirane',
								label: 'Europe/Tirane',
							},
							{
								id: 'Europe/Tiraspol',
								label: 'Europe/Tiraspol',
							},
							{
								id: 'Europe/Ulyanovsk',
								label: 'Europe/Ulyanovsk',
							},
							{
								id: 'Europe/Uzhgorod',
								label: 'Europe/Uzhgorod',
							},
							{
								id: 'Europe/Vaduz',
								label: 'Europe/Vaduz',
							},
							{
								id: 'Europe/Vatican',
								label: 'Europe/Vatican',
							},
							{
								id: 'Europe/Vienna',
								label: 'Europe/Vienna',
							},
							{
								id: 'Europe/Vilnius',
								label: 'Europe/Vilnius',
							},
							{
								id: 'Europe/Volgograd',
								label: 'Europe/Volgograd',
							},
							{
								id: 'Europe/Warsaw',
								label: 'Europe/Warsaw',
							},
							{
								id: 'Europe/Zagreb',
								label: 'Europe/Zagreb',
							},
							{
								id: 'Europe/Zaporozhye',
								label: 'Europe/Zaporozhye',
							},
							{
								id: 'Europe/Zurich',
								label: 'Europe/Zurich',
							},
							{
								id: 'GB',
								label: 'GB',
							},
							{
								id: 'GB-Eire',
								label: 'GB-Eire',
							},
							{
								id: 'GMT',
								label: 'GMT',
							},
							{
								id: 'GMT+0',
								label: 'GMT+0',
							},
							{
								id: 'GMT-0',
								label: 'GMT-0',
							},
							{
								id: 'GMT0',
								label: 'GMT0',
							},
							{
								id: 'Greenwich',
								label: 'Greenwich',
							},
							{
								id: 'HST',
								label: 'HST',
							},
							{
								id: 'Hongkong',
								label: 'Hongkong',
							},
							{
								id: 'Iceland',
								label: 'Iceland',
							},
							{
								id: 'Indian/Antananarivo',
								label: 'Indian/Antananarivo',
							},
							{
								id: 'Indian/Chagos',
								label: 'Indian/Chagos',
							},
							{
								id: 'Indian/Christmas',
								label: 'Indian/Christmas',
							},
							{
								id: 'Indian/Cocos',
								label: 'Indian/Cocos',
							},
							{
								id: 'Indian/Comoro',
								label: 'Indian/Comoro',
							},
							{
								id: 'Indian/Kerguelen',
								label: 'Indian/Kerguelen',
							},
							{
								id: 'Indian/Mahe',
								label: 'Indian/Mahe',
							},
							{
								id: 'Indian/Maldives',
								label: 'Indian/Maldives',
							},
							{
								id: 'Indian/Mauritius',
								label: 'Indian/Mauritius',
							},
							{
								id: 'Indian/Mayotte',
								label: 'Indian/Mayotte',
							},
							{
								id: 'Indian/Reunion',
								label: 'Indian/Reunion',
							},
							{
								id: 'Iran',
								label: 'Iran',
							},
							{
								id: 'Israel',
								label: 'Israel',
							},
							{
								id: 'Jamaica',
								label: 'Jamaica',
							},
							{
								id: 'Japan',
								label: 'Japan',
							},
							{
								id: 'Kwajalein',
								label: 'Kwajalein',
							},
							{
								id: 'Libya',
								label: 'Libya',
							},
							{
								id: 'MET',
								label: 'MET',
							},
							{
								id: 'MST',
								label: 'MST',
							},
							{
								id: 'MST7MDT',
								label: 'MST7MDT',
							},
							{
								id: 'Mexico/BajaNorte',
								label: 'Mexico/BajaNorte',
							},
							{
								id: 'Mexico/BajaSur',
								label: 'Mexico/BajaSur',
							},
							{
								id: 'Mexico/General',
								label: 'Mexico/General',
							},
							{
								id: 'NZ',
								label: 'NZ',
							},
							{
								id: 'NZ-CHAT',
								label: 'NZ-CHAT',
							},
							{
								id: 'Navajo',
								label: 'Navajo',
							},
							{
								id: 'PRC',
								label: 'PRC',
							},
							{
								id: 'PST8PDT',
								label: 'PST8PDT',
							},
							{
								id: 'Pacific/Apia',
								label: 'Pacific/Apia',
							},
							{
								id: 'Pacific/Auckland',
								label: 'Pacific/Auckland',
							},
							{
								id: 'Pacific/Bougainville',
								label: 'Pacific/Bougainville',
							},
							{
								id: 'Pacific/Chatham',
								label: 'Pacific/Chatham',
							},
							{
								id: 'Pacific/Chuuk',
								label: 'Pacific/Chuuk',
							},
							{
								id: 'Pacific/Easter',
								label: 'Pacific/Easter',
							},
							{
								id: 'Pacific/Efate',
								label: 'Pacific/Efate',
							},
							{
								id: 'Pacific/Enderbury',
								label: 'Pacific/Enderbury',
							},
							{
								id: 'Pacific/Fakaofo',
								label: 'Pacific/Fakaofo',
							},
							{
								id: 'Pacific/Fiji',
								label: 'Pacific/Fiji',
							},
							{
								id: 'Pacific/Funafuti',
								label: 'Pacific/Funafuti',
							},
							{
								id: 'Pacific/Galapagos',
								label: 'Pacific/Galapagos',
							},
							{
								id: 'Pacific/Gambier',
								label: 'Pacific/Gambier',
							},
							{
								id: 'Pacific/Guadalcanal',
								label: 'Pacific/Guadalcanal',
							},
							{
								id: 'Pacific/Guam',
								label: 'Pacific/Guam',
							},
							{
								id: 'Pacific/Honolulu',
								label: 'Pacific/Honolulu',
							},
							{
								id: 'Pacific/Johnston',
								label: 'Pacific/Johnston',
							},
							{
								id: 'Pacific/Kanton',
								label: 'Pacific/Kanton',
							},
							{
								id: 'Pacific/Kiritimati',
								label: 'Pacific/Kiritimati',
							},
							{
								id: 'Pacific/Kosrae',
								label: 'Pacific/Kosrae',
							},
							{
								id: 'Pacific/Kwajalein',
								label: 'Pacific/Kwajalein',
							},
							{
								id: 'Pacific/Majuro',
								label: 'Pacific/Majuro',
							},
							{
								id: 'Pacific/Marquesas',
								label: 'Pacific/Marquesas',
							},
							{
								id: 'Pacific/Midway',
								label: 'Pacific/Midway',
							},
							{
								id: 'Pacific/Nauru',
								label: 'Pacific/Nauru',
							},
							{
								id: 'Pacific/Niue',
								label: 'Pacific/Niue',
							},
							{
								id: 'Pacific/Norfolk',
								label: 'Pacific/Norfolk',
							},
							{
								id: 'Pacific/Noumea',
								label: 'Pacific/Noumea',
							},
							{
								id: 'Pacific/Pago_Pago',
								label: 'Pacific/Pago_Pago',
							},
							{
								id: 'Pacific/Palau',
								label: 'Pacific/Palau',
							},
							{
								id: 'Pacific/Pitcairn',
								label: 'Pacific/Pitcairn',
							},
							{
								id: 'Pacific/Pohnpei',
								label: 'Pacific/Pohnpei',
							},
							{
								id: 'Pacific/Ponape',
								label: 'Pacific/Ponape',
							},
							{
								id: 'Pacific/Port_Moresby',
								label: 'Pacific/Port_Moresby',
							},
							{
								id: 'Pacific/Rarotonga',
								label: 'Pacific/Rarotonga',
							},
							{
								id: 'Pacific/Saipan',
								label: 'Pacific/Saipan',
							},
							{
								id: 'Pacific/Samoa',
								label: 'Pacific/Samoa',
							},
							{
								id: 'Pacific/Tahiti',
								label: 'Pacific/Tahiti',
							},
							{
								id: 'Pacific/Tarawa',
								label: 'Pacific/Tarawa',
							},
							{
								id: 'Pacific/Tongatapu',
								label: 'Pacific/Tongatapu',
							},
							{
								id: 'Pacific/Truk',
								label: 'Pacific/Truk',
							},
							{
								id: 'Pacific/Wake',
								label: 'Pacific/Wake',
							},
							{
								id: 'Pacific/Wallis',
								label: 'Pacific/Wallis',
							},
							{
								id: 'Pacific/Yap',
								label: 'Pacific/Yap',
							},
							{
								id: 'Poland',
								label: 'Poland',
							},
							{
								id: 'Portugal',
								label: 'Portugal',
							},
							{
								id: 'ROC',
								label: 'ROC',
							},
							{
								id: 'ROK',
								label: 'ROK',
							},
							{
								id: 'Singapore',
								label: 'Singapore',
							},
							{
								id: 'Turkey',
								label: 'Turkey',
							},
							{
								id: 'UCT',
								label: 'UCT',
							},
							{
								id: 'US/Alaska',
								label: 'US/Alaska',
							},
							{
								id: 'US/Aleutian',
								label: 'US/Aleutian',
							},
							{
								id: 'US/Arizona',
								label: 'US/Arizona',
							},
							{
								id: 'US/Central',
								label: 'US/Central',
							},
							{
								id: 'US/East-Indiana',
								label: 'US/East-Indiana',
							},
							{
								id: 'US/Eastern',
								label: 'US/Eastern',
							},
							{
								id: 'US/Hawaii',
								label: 'US/Hawaii',
							},
							{
								id: 'US/Indiana-Starke',
								label: 'US/Indiana-Starke',
							},
							{
								id: 'US/Michigan',
								label: 'US/Michigan',
							},
							{
								id: 'US/Mountain',
								label: 'US/Mountain',
							},
							{
								id: 'US/Pacific',
								label: 'US/Pacific',
							},
							{
								id: 'US/Samoa',
								label: 'US/Samoa',
							},
							{
								id: 'UTC',
								label: 'UTC',
							},
							{
								id: 'Universal',
								label: 'Universal',
							},
							{
								id: 'W-SU',
								label: 'W-SU',
							},
							{
								id: 'WET',
								label: 'WET',
							},
							{
								id: 'Zulu',
								label: 'Zulu',
							},
						],
						datetime_formats: [
							{
								id: '%d %b %Y %H:%M',
								label: '04 Oct 2017 13:48',
							},
							{
								id: '%d %b %Y %I:%M %p',
								label: '04 Oct 2017 01:48 PM',
							},
							{
								id: '%d %B %Y %H:%M',
								label: '04 October 2017 13:48',
							},
							{
								id: '%d %B %Y %I:%M %p',
								label: '04 October 2017 01:48 PM',
							},
							{
								id: '%d/%m/%Y %H:%M',
								label: '04/10/2017 13:48',
							},
							{
								id: '%d/%m/%y %I:%M %p',
								label: '04/10/17 01:48 PM',
							},
							{
								id: '%m/%d/%y %H:%M',
								label: '10/04/17 13:48',
							},
							{
								id: '%d/%m/%Y %I:%M %p',
								label: '04/10/2017 01:48 PM',
							},
						],
					},
					message: 'Success',
				},
			})
		);
	}),

	rest.put('/api/v1/apps/:appId/', (req, res, ctx) => {
		return res(
			ctx.delay(500),
			ctx.status(200),
			ctx.json({
				success: true,
				response: {
					message: 'Success',
				},
			})
		);
	}),
];
