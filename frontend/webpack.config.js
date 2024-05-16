const metadata = require('./src/metadata.json');
const path = require('path');
const UglifyJsPlugin = require('uglifyjs-webpack-plugin');
const glob = require('glob');
module.exports = {
	entry: {
		'bundle.js': glob
			.sync('build/static/?(js|css)/main.*.?(js|css)')
			.map((f) => path.resolve(__dirname, f)),
	},
	output: {
		path: path.resolve(__dirname, '../backend/src/zango/assets/app_panel/js'),
		filename: `build.v${metadata.buildMajor}.${metadata.buildMinor}.${metadata.buildPatch}.min.js`,
	},
	module: {
		rules: [
			{
				test: /\.css$/,
				use: ['style-loader', 'css-loader'],
			},
		],
	},
	plugins: [new UglifyJsPlugin()],
};
