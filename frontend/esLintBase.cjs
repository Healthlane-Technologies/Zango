module.exports = {
	parserOptions: {
		ecmaVersion: 2020,
	},
	extends: [
		'airbnb-base',
		'eslint:recommended',
		'plugin:prettier/recommended',
		'plugin:import/recommended',
	],
	env: {
		es6: true,
		jest: true,
		node: true,
	},
	rules: {
		strict: ['error', 'global'],
		'no-return-await': 'error',
		'object-shorthand': [
			'error',
			'always',
			{ avoidExplicitReturnArrows: true },
		],
		'class-methods-use-this': 'off',
		// 'max-classes-per-file': 'warn',
		'default-param-last': 'warn',
		'no-template-curly-in-string': 'warn',
	},
};
