const metadata = require('./src/metadata.json');
const path = require('path');
const TerserPlugin = require('terser-webpack-plugin');
const glob = require('glob');
module.exports = {
	entry: {
		'bundle.js': glob
			.sync('build/static/?(js|css)/main.*.?(js|css)')
			.map((f) => path.resolve(__dirname, f)),
	},
	output: {
		path: path.resolve(__dirname, '../backend/src/zango/assets/app_panel/js'),
		filename: `build.${Date.now()}.min.js`,
	},
	module: {
		rules: [
			{
				test: /\.css$/,
				use: ['style-loader', 'css-loader'],
			},
		],
	},
	optimization: {
		minimize: true,
		minimizer: [new TerserPlugin()],
	},
	resolve: {
		alias: {
			react: path.resolve('./node_modules/react'),
			'react-dom': path.resolve('./node_modules/react-dom'),
		},
	},
};
