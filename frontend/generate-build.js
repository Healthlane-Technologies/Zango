var fs = require('fs');
fs.readFile('src/metadata.json', function (err, content) {
	if (err) throw err;
	var metadata = JSON.parse(content);
	metadata.buildPatch = metadata.buildPatch + 1;
	fs.writeFile('src/metadata.json', JSON.stringify(metadata), function (err) {
		if (err) throw err;
		console.log(
			`Current build number: ${metadata.buildMajor}.${metadata.buildMinor}.${metadata.buildPatch} ${metadata.buildTag}`
		);
	});
});
