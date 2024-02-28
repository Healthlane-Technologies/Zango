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
		publicPath: '/',
		filename: `build/static/js/${metadata.buildMajor}.${metadata.buildMinor}.${metadata.buildPatch}/build.v${metadata.buildMajor}.${metadata.buildMinor}.${metadata.buildPatch}.min.js`,
		// filename: `build/static/js/build.min.js`,
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
