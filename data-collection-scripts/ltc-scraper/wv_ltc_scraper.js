const { chromium } = require('playwright');
const fastcsv = require('fast-csv');

(async (callbackfn, thisArg) => {
  const URL = 'https://dhhr.wv.gov/COVID-19/Pages/default.aspx'
  // some setup
  const browser = await chromium.launch({
    headless: true
  })
  const context = await browser.newContext({ recordVideo: { dir: 'videos/' } })
  const page = await context.newPage()

  // load the frame and the LTC tab
  await page.goto(URL)

  const frame = await page.frame({url: /app\.powerbigov\.us/})
  await frame.click('//button[normalize-space(.)=\'Long-Term Care\']')

  // helper function to turn an array of cell elements into an array of text, meant for $$eval
  const arrCellsToText = (elems) => {
    return elems.map(elem => elem.innerText.trim())
  }

  // get the table column headers
  await frame.waitForSelector('.columnHeaders > div > div')
  const columnHeaders = await frame.$$eval('.columnHeaders > div > div', arrCellsToText)

  // this big function collects all visible data from the table in a big 2D array
  // with one row for each facility and columns for each field tracked
  const dataFromTable = async () => {
    // Here's where it gets downright weird because the frame structure is so...special
    // The data table is organized into four divs: left/top, right/top, left/bottom, right/bottom
    // As we scroll, these get moved around and populated.

    // this gets us the left half of the table. each entry in the array is a column div
    // there will be more of these than there are columns because we get both left/top and left/bottom
    // tangled together here
    const elemColsLeft = await frame.$$('.bodyCells > div > div[style*="left:0"] > div')
    // and this gets us the right half of the table
    const elemColsRight = await frame.$$('.bodyCells > div > div:not([style*="left:0"]) > div')

    // collect all the data out of the left column elements
    let dataColsTangled = []
    for (const elemCol of elemColsLeft) {
      const dataCol = await elemCol.$$eval('.pivotTableCellWrap', arrCellsToText)
      dataColsTangled.push(dataCol)
    }

    // the catch is that dataColsTangled repeats itself because we processed the top and bottom of the table together
    // (e.g. it now looks like [col1, col2, col3, col1, col2, col3])

    // so now we're going to do the right side, but we need to do some extra nonsense to insert col4 in the right places
    // in that sequence, giving us [col1, col2, col3, col4, col1, col2, col3, col4]
    for (const [index, elemCol] of elemColsRight.entries()) {
      const dataCol = await elemCol.$$eval('.pivotTableCellWrap', arrCellsToText)
      // insert the new right-side column where it belongs (either after left/top or after left/bottom)
      dataColsTangled.splice((columnHeaders.length * (index + 1)) - 1, 0, dataCol)
    }

    // we've got left, right, top, and bottom now! wasn't that fun? (no)
    // but they look like [col1-top, col2-top, col3-top, col4-top, col1-bottom, col2-bottom, col3-bottom, col4-bottom],
    // so we'll untangle that, constructing dataCols to be a totally normal [col1, col2, col3, col4]
    const dataCols = []
    dataColsTangled.forEach((dataCol, i) => {
      const curColIndex = i % columnHeaders.length
      dataCols[curColIndex] = dataCols[curColIndex] === undefined ? dataCol : dataCols[curColIndex].concat(dataCol)
    })

    // transpose dataCols so we get a nice normal 2D array where each row is a facility and columns are data columns
    // thanks to https://stackoverflow.com/a/36164530
    const transpose = m => m[0].map((x, i) => m.map(x => x[i]))
    const dataArr = transpose(dataCols)

    // and we'll turn that into an object, e.g. {facilityName => {County: abc, Active Positive Residents: 2, etc...}}
    const data = {}
    dataArr.map((dataElem, i) => {
      const facilityName = dataElem[1]
      const facilityData = {}
      for (const [colIndex, colHeader] of columnHeaders.entries()) {
        facilityData[colHeader] = dataElem[colIndex]
      }
      data[facilityName] = facilityData
    })
    return data
  }

  // ok let's go. we'll grab all the visible data, add it to `data`, scroll down, and keep doing that until
  // no new data is emerging, which means we're at the bottom
  let data = {}
  let lastNumFacilities = -1
  while (Object.keys(data).length  != lastNumFacilities) {
    lastNumFacilities = Object.keys(data).length

    const visibleData = await dataFromTable()
    data = {...data, ...visibleData}

    // click the down scroll button a whole bunch of times to get more data
    const elemScrollDown = await frame.$('.scroll-bar-div:not([style*="visibility: hidden"]) .scroll-bar-part-arrow:nth-child(2)')
    for (const i of Array.from(Array(45))) {
      await elemScrollDown.click()
    }
    await frame.waitForTimeout(2000)
  }

  // output all the data to stdout in csv format
  const csvStream = fastcsv.format({ headers: true })
  csvStream.pipe(process.stdout).on('end', () => process.exit());
  for (const facilityData of Object.values(data)) {
    csvStream.write(facilityData)
  }
  csvStream.end();

  // cleanup
  await page.close();
  await context.close();
  await browser.close();
})().catch((ex) => {console.error(ex); process.exit(1)});
