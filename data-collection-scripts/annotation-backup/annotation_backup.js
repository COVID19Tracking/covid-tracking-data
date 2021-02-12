const Airtable = require('airtable');
const fastcsv = require('fast-csv');

(async () => {
  const base = new Airtable().base('app2tJkNU6YXNrDwc');
  const allRecords = []

  // ask airtable for all the rows from the desired view
  await base('Annotations').select({
    view: "all-annotations-anon"
  }).eachPage(function page(records, fetchNextPage) {
    // for whatever odd reason, the api calls this callback for each page of rows returned, and then returns the
    // promise once all pages have been retrieved. so we'll just store every page as we go
    allRecords.push(...records)
    fetchNextPage();
  })

  const headers = [
      "/id",
      "/fields/Annotation Summary",
      "/fields/State",
      "/fields/States Daily Column",
      "/fields/Metric",
      "/fields/Annotation",
      "/fields/Evidence For",
      "/fields/Evidence Type",
      "/fields/Evidence",
      "/fields/Evidence Source Link",
      "/fields/Last Checked",
      "/createdTime",
      "/fields/Media/Outreach As Of",
      "/fields/Media/Outreach Out of Date",
      "/fields/MetricTitle",
      "/fields/Excludes"]


  // go through all the records and output them in CSV format with the desired column order
  const csvStream = fastcsv.format({headers: headers})
  csvStream.pipe(process.stdout).on('end', () => process.exit());
  for (let record of allRecords) {
    record = record._rawJson
    const data = [
      record.id,
      record.fields["Annotation Summary"],
      record.fields["State"],
      record.fields["States Daily Column"],
      record.fields["Metric"],
      record.fields["Annotation"],
      record.fields["Evidence For"],
      record.fields["Evidence Type"],
      record.fields["Evidence"],
      record.fields["Evidence Source Link"],
      record.fields["Last Checked"],
      record.createdTime,
      record.fields["Media/Outreach As Of"],
      record.fields["Media/Outreach Out of Date"],
      record.fields["MetricTitle"],
      record.fields["Excludes"],
    ]
    csvStream.write(data)
  }
  csvStream.end();

})().catch((ex) => {
  console.error(ex);
  process.exit(1)
});
