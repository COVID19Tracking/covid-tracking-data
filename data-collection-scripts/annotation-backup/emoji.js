const fetch = require('node-fetch');
const fastcsv = require('fast-csv');

(async () => {
  const emoji = []

  for (let page=1; page < 25; page++) {
    await fetch("https://covid-tracking.slack.com/api/emoji.adminList?_x_id=e0fc1ead-1613119689.547&slack_route=TUPV6BFR9&_x_version_ts=no-version", {
      "credentials": "include",
      "headers": {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.16; rv:86.0) Gecko/20100101 Firefox/86.0",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "Content-Type": "multipart/form-data; boundary=---------------------------295723995310212772601835899689"
      },
      "body": "-----------------------------295723995310212772601835899689\r\nContent-Disposition: form-data; name=\"page\"\r\n\r\n" + page + "\r\n-----------------------------295723995310212772601835899689\r\nContent-Disposition: form-data; name=\"count\"\r\n\r\n100\r\n-----------------------------295723995310212772601835899689\r\nContent-Disposition: form-data; name=\"sort_by\"\r\n\r\ncreated\r\n-----------------------------295723995310212772601835899689\r\nContent-Disposition: form-data; name=\"sort_dir\"\r\n\r\nasc\r\n-----------------------------295723995310212772601835899689\r\nContent-Disposition: form-data; name=\"token\"\r\n\r\nxoxs-975992389859-987646014741-1076864126150-fbe7ced80e58e0eb5228c50af624c8588440958622da716484aa04204b974c36\r\n-----------------------------295723995310212772601835899689\r\nContent-Disposition: form-data; name=\"_x_reason\"\r\n\r\ncustomize-emoji-next-page\r\n-----------------------------295723995310212772601835899689\r\nContent-Disposition: form-data; name=\"_x_mode\"\r\n\r\nonline\r\n-----------------------------295723995310212772601835899689--\r\n",
      "method": "POST",
      "mode": "cors"
    }).then(res => res.json())
    .then(json => emoji.push(...json["emoji"]))
  }
  const csvStream = fastcsv.format({headers: true})
  csvStream.pipe(process.stdout).on('end', () => process.exit());
  for (let e of Object.values(emoji)) {
    csvStream.write(e)
  }
  csvStream.end();
})().catch((ex) => {
  console.error(ex)
  process.exit(1)
});