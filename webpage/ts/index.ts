/**
 * index.ts : History page functionality and interactivity.
 * @author Iwan Mitchell
 */

import { displayChart } from "./charting";
import { BidData, EnergyData, ProcessData, ReportDay, ReportMonth, ReportMonths, RequestBids, RequestDates, RequestEnergy, ResponseRegistry, ValidateResponse } from "./requests";
import { MonthNames } from "./utils";

// HTML Elements
let ChartEnergyNet: HTMLCanvasElement;
let ChartEnergyTotal: HTMLCanvasElement;
let ChartEnergySolar: HTMLCanvasElement;
let ChartEnergyWind: HTMLCanvasElement;
let ChartMarket: HTMLCanvasElement;

let HistoryDates: HTMLElement;
let DateTitle: HTMLTitleElement;

let CarbonCard: HTMLElement;
let ProfitCard: HTMLElement;

let BidTable: HTMLTableElement;

let ButtonDownload: HTMLButtonElement;
let overlayLoading: HTMLDivElement;

// Page variables
let PageDate: string;
let Today: string;
let PageType: DateType;
let HasBidData: boolean;
let HasEnergyData: boolean;
let flagLoading: number;

// Cached Data
let Dates: ReportMonths;
let Energy: EnergyData;
let Bids: BidData;

/**
 * Type of date the page is displaying.
 */
enum DateType {
	/**
	 * Page is displaying an overview of just one day.
	 */
	Day = "day",
	/**
	 * Page is displaying an overview of the entire month.
	 */
	Month = "month",
}

/**
 * Skeleton sections
 */
enum SkeletonType {
	Energy = "energy",
	Market = "market",
	Dates = "dates",
}

/**
 * Skeleton states
 */
enum SkeletonState {
	Hidden = "hidden",
	Visible = "visible",
	Error = "error"
}

/**
 * Toggles displaying content skeletons rather than content.
 *
 * Todo: trigger element displays using maps, rather than duplicated switch statements.
 *
 * @param show - If true, show skeletons and hide content.
 * @param type - Type of skeletons to show
 */
function skeletons(show: SkeletonState, type: SkeletonType): void {

	// Due to how ts/js works, anything defined in a single switch case, is
	// actually in the scope of the entire switch statement. We define these
	// variables outside of this scope, to prevent any uninitialized errors.
	const skeletonsError = document?.getElementsByClassName(type.toString() + "-skeleton");
	const skeletonsShow = document?.getElementsByClassName(type.toString() + "-skeleton");
	const skeletonsHide = document?.getElementsByClassName(type.toString() + "-skeleton");

	switch (show) {
	case SkeletonState.Visible:
		switch (type) {
		case SkeletonType.Energy:
			ChartEnergySolar.classList.add("hidden");
			ChartEnergyWind.classList.add("hidden");
			ChartEnergyTotal.classList.add("hidden");
			ChartEnergyNet.classList.add("hidden");
			break;
		case SkeletonType.Market:
			ChartMarket.classList.add("hidden");
			break;
		case SkeletonType.Dates:
			HistoryDates.classList.add("hidden");
			break;
		default:
			break;
		}

		// Show normal skeletons
		for (let i = 0; i < skeletonsShow.length; i++) {
			const skeleton = skeletonsShow[i];
			skeleton.setAttribute("effect", "pulse");
			skeleton.classList.remove("hidden");
			skeleton.classList.remove("error");
		}
		break;
	case SkeletonState.Error:
		switch (type) {
		case SkeletonType.Energy:
			ChartEnergySolar.classList.add("hidden");
			ChartEnergyWind.classList.add("hidden");
			ChartEnergyTotal.classList.add("hidden");
			ChartEnergyNet.classList.add("hidden");
			break;
		case SkeletonType.Market:
			ChartMarket.classList.add("hidden");
			break;
		case SkeletonType.Dates:
			HistoryDates.classList.add("hidden");
			break;
		default:
			break;
		}

		// Show Error Skeletons
		for (let i = 0; i < skeletonsError.length; i++) {
			const skeleton = skeletonsError[i];
			skeleton.setAttribute("effect", "sheen");
			skeleton.classList.remove("hidden");
			skeleton.classList.add("error");
		}
		break;
	default:
	case SkeletonState.Hidden:
		switch (type) {
		case SkeletonType.Energy:
			ChartEnergySolar.classList.remove("hidden");
			ChartEnergyWind.classList.remove("hidden");
			ChartEnergyTotal.classList.remove("hidden");
			ChartEnergyNet.classList.remove("hidden");
			break;
		case SkeletonType.Market:
			ChartMarket.classList.remove("hidden");
			break;
		case SkeletonType.Dates:
			HistoryDates.classList.remove("hidden");
			break;
		default:
			break;
		}

		// Hide skeletons
		for (let i = 0; i < skeletonsHide.length; i++) {
			const skeleton = skeletonsHide[i];
			skeleton.classList.add("hidden");
		}
		break;
	}
}

/**
 * Populate aside with dates containing reports.
 * @param dates  - Report Dates to create
 */
function CreateDates(dates: ReportMonths): void {
	dates.forEach(month => {
		// Month tag (small number in title text)
		const monthDetailsSummaryTag = document.createElement("sl-tag");
		monthDetailsSummaryTag.setAttribute("size", "small");
		monthDetailsSummaryTag.setAttribute("type", "info");
		monthDetailsSummaryTag.setAttribute("pill", "");
		monthDetailsSummaryTag.textContent = month.days.length.toString();

		// Month Summary text (Month Name)
		const monthDetailsSummaryText = document.createElement("p");
		monthDetailsSummaryText.textContent = month.name;
		monthDetailsSummaryText.appendChild(monthDetailsSummaryTag);

		// Month Summary Container (Month Name)
		const monthDetailsSummary = document.createElement("div");
		monthDetailsSummary.setAttribute("slot", "summary");
		monthDetailsSummary.appendChild(monthDetailsSummaryText);

		// Month Container
		const monthDetails = document.createElement("sl-details");
		monthDetails.appendChild(monthDetailsSummary);

		const linkList = document.createElement("ol");

		const overviewListItem = document.createElement("li");
		const overviewLink = document.createElement("a");
		overviewLink.text = month.name + " Overview";
		overviewLink.onclick = () => {
			ChangeDate(month.date);
		};
		overviewListItem.appendChild(overviewLink);
		linkList.appendChild(overviewListItem);

		month.days.forEach(day => {
			const listItem = document.createElement("li");
			const link = document.createElement("a");
			link.text = month.year + "-" + month.name + "-" + day.day.toString().padStart(2, "0");
			link.onclick = () => {
				ChangeDate(day.date);
			};
			listItem.appendChild(link);
			linkList.appendChild(listItem);
		});
		monthDetails.appendChild(linkList);
		HistoryDates?.appendChild(monthDetails);
	});
}

/**
 * Change the date of the page to a new date. This results in requesting new
 * energy and marketing data.
 * @param date - ISO Date to change to (2021-07-22)
 */
function ChangeDate(date: string): void {
	if (!ValidateDate(date)) {
		// ChangeDate is also called from link callbacks, so just make sure date
		// is not random data.
		console.error("Invalid Date from JavaScript: " + date);
		return;
	}

	console.info("Changing date to " + date);

	PageType = date.length == 7 ? DateType.Month : DateType.Day;

	PageDate = date;
	UpdatePage();

	// Only update energy and market data, we assume dates aren't changing
	// halfway through a session.
	flagLoading = 1;
	markLoading();
	RequestEnergy(date).then((response: Response) => {
		console.log("Energy Response Status:" + response.status);
		const result = response.json();

		result.then((result: unknown) => {
			if (!ValidateResponse(result, "energy")) {
				console.error("Invalid api response from energy endpoint");
				console.error(result);
				return;
			}

			// Success, data is real!
			Energy = ProcessData["energy"](result as ResponseRegistry["energy"]);
			HasEnergyData = true;

			// Change data labels to match Day or Month mode

			const newTimes: Array<string> = [];
			if (PageType == DateType.Day) {
				// Day, so just concat into times
				Energy.times.forEach(time => {
					// 2021-09-02 23:00:00+00:00
					newTimes.push(time.slice(11, 16));
				});
			} else {
				// Month, so just remove second and offset
				Energy.times.forEach(time => {
					// 2021-09-02 23:00:00+00:00
					newTimes.push(time.slice(0, 16));
				});
			}
			Energy.times = newTimes;

			// Update charts
			displayChart["windPower"](ChartEnergyWind, Energy);
			displayChart["solarPower"](ChartEnergySolar, Energy);
			displayChart["overviewPower"](ChartEnergyTotal, Energy);
			displayChart["netPower"](ChartEnergyNet, Energy);

			// Update carbon card
			UpdateCarbonCard(Energy);

			// Remove skeletons
			skeletons(SkeletonState.Hidden, SkeletonType.Energy);
		}).catch((reason: unknown) => {
			console.error("Error parsing energy data");
			console.error(response);
			console.error(reason);
			HasEnergyData = false;
			UpdateCarbonCard(null);
			skeletons(SkeletonState.Error, SkeletonType.Energy);
		}).finally(() => {
			markLoaded();
		});
	}).catch((reason: unknown) => {
		console.error("Error requesting energy data");
		console.error(reason);
		HasEnergyData = false;
		UpdateCarbonCard(null);
		skeletons(SkeletonState.Error, SkeletonType.Energy);
		markLoaded();
	});
	RequestBids(date).then((response: Response) => {
		console.log("Bid Response Status:" + response.status);
		const result = response.json();

		result.then((result: unknown) => {
			if (!ValidateResponse(result, "bids")) {
				console.error("Invalid api response from bids endpoint");
				console.error(result);
				return;
			}

			// Success, data is real!
			Bids = ProcessData["bids"](result as ResponseRegistry["bids"]);
			HasBidData = true;

			// Update charts
			displayChart["overviewMarket"](ChartMarket, Bids);

			// Update profit card
			UpdateProfitCard(Bids);

			// Update table of bids
			UpdateBidTable(Bids);

			// Remove skeletons
			skeletons(SkeletonState.Hidden, SkeletonType.Market);
		}).catch((reason: unknown) => {
			console.error("Error parsing bids");
			console.error(reason);
			console.error(response);
			HasBidData = false;
			UpdateProfitCard(null);
			skeletons(SkeletonState.Error, SkeletonType.Market);
		}).finally(() => {
			markLoaded();
		});
	}).catch((reason: unknown) => {
		console.error("Error requesting bids");
		console.error(reason);
		HasBidData = false;
		UpdateProfitCard(null);

		skeletons(SkeletonState.Error, SkeletonType.Market);
		markLoaded();
	});
}

/**
 * Update the carbon saved card
 * @param data - Energy Data
 */
function UpdateCarbonCard(data: EnergyData | null): void {
	// Remove all children and classes
	CarbonCard.textContent = "";
	CarbonCard.classList.remove("danger");
	CarbonCard.classList.remove("success");

	// Create title
	const title = document.createElement("p");
	title.textContent = "Carbon Saved";

	// Create real carbon saved
	const real = document.createElement("h1");
	if (data !== null) {
		real.textContent = Intl.NumberFormat("en-gb").format(Math.round(data.realCarbonSaved / 1000)) + " kgCO2";
		CarbonCard.classList.add((data.realCarbonSaved + "")[0] == "-" ? "danger" : "success");
	} else {
		real.textContent = "No Data";
	}

	// Create predicted carbon saved
	const predicted = document.createElement("p");

	// (don't ask, please...)
	if (data !== null) {
		predicted.classList.add((data.predictedCarbonSaved + "")[0] == "-" ? "danger" : "success");
		predicted.textContent = Intl.NumberFormat("en-gb").format(Math.round(data.predictedCarbonSaved / 1000)) + " kgCO2";
	} else {
		predicted.textContent = "No Data";
	}

	// Add all to card
	CarbonCard.appendChild(title);
	CarbonCard.appendChild(real);
	CarbonCard.appendChild(predicted);
}

/**
 * Update the profit saved card
 * @param data - Energy Data
 */
function UpdateProfitCard(data: BidData | null): void {
	const noData = (data === null);

	// Remove all children and classes
	ProfitCard.textContent = "";
	ProfitCard.classList.remove("danger");
	ProfitCard.classList.remove("success");

	// Create title
	const title = document.createElement("p");
	title.textContent = "Estimated Bid Profit";

	// Create real Profit saved
	const real = document.createElement("h1");
	if (data !== null) {
		real.textContent = noData ? "No Data" : "£" + Intl.NumberFormat("en-gb").format(data.profit);
		ProfitCard.classList.add((data.profit + "")[0] == "-" ? "danger" : "success");
	} else {
		real.textContent = "No Data";
	}

	// Create predicted Profit saved
	const predicted = document.createElement("p");

	// Add all to card
	ProfitCard.appendChild(title);
	ProfitCard.appendChild(real);
	ProfitCard.appendChild(predicted);
}

function UpdateBidTable(data: BidData): void {
	BidTable.textContent = "";
	const thead = BidTable.createTHead();

	const dateHead = document.createElement("th");
	dateHead.textContent = "Date";
	thead.appendChild(dateHead);

	const hourHead = document.createElement("th");
	hourHead.textContent = "Hour";
	thead.appendChild(hourHead);

	const typeHead = document.createElement("th");
	typeHead.textContent = "Type";
	thead.appendChild(typeHead);

	const volumeHead = document.createElement("th");
	volumeHead.textContent = "Volume (MW-h)";
	thead.appendChild(volumeHead);

	const priceHead = document.createElement("th");
	priceHead.textContent = "Price Per MW-h (£)";
	thead.appendChild(priceHead);

	const totalHead = document.createElement("th");
	totalHead.textContent = "Bid Total (£)";
	thead.appendChild(totalHead);

	data.bids.forEach(bid => {
		const row = document.createElement("tr");

		const dateRow = document.createElement("td");
		dateRow.textContent = bid.date;
		row.appendChild(dateRow);

		const hourRow = document.createElement("td");
		hourRow.textContent = bid.hour + "";
		row.appendChild(hourRow);

		const typeRow = document.createElement("td");
		const typeTag = document.createElement("sl-tag");
		typeTag.textContent = bid.type.toString();
		typeTag.setAttribute("type", bid.type.toString() == "BUY" ? "warning" : "success");
		typeTag.setAttribute("size", "small");
		typeRow.appendChild(typeTag);
		row.appendChild(typeRow);

		const volumeRow = document.createElement("td");
		volumeRow.textContent = bid.volume + "";
		row.appendChild(volumeRow);

		const priceRow = document.createElement("td");
		priceRow.textContent = "£" + Intl.NumberFormat("en-gb").format(bid.price);
		row.appendChild(priceRow);

		const totalRow = document.createElement("td");
		totalRow.textContent = "£" + Intl.NumberFormat("en-gb").format(bid.price * bid.volume);
		row.appendChild(totalRow);

		BidTable.appendChild(row);
	});
}

/**
 * Update page details, such as title, url, headers, etc.
 */
function UpdatePage(): void {
	const dateSplit = PageDate.split("-");
	const monthText = MonthNames[(+dateSplit[1]) - 1];

	// Update header Text
	if (DateTitle != null) {
		DateTitle.innerText = PageType == DateType.Day ? dateSplit[0] + "-" + monthText + "-" + dateSplit[2] : monthText + " Overview";
	}

	// Update URL
	window.history.replaceState("", "", window.location.href.split("?")[0] + "?date=" + PageDate);

	// Update page title
	document.title = "Report | " + PageDate;
}

/**
 * Check to see if the given date is in a valid format.
 * @param date - Potential date string
 * @returns True if the date is a valid ISO format, with or without a day ('2021-07' and '2021-07-22')
 */
function ValidateDate(date: string): boolean {
	if (date.length < 6) {
		return false;
	}

	if (date.length > 10) {
		return false;
	}

	// try parsing url parameter as a date
	const split: Array<string> = date.split("-");

	// Check size formats
	if (!(split.length == 2 || split.length == 3)) {
		return false;
	}
	if (split[0].length != 4) {
		return false;
	}
	if (split[1].length > 2 || split[1].length == 0) {
		return false;
	}

	if (split.length == 3) {
		// Check for day
		if (split[2].length > 2 || split[2].length == 0) {
			return false;
		}
	}

	// Check values
	if (+split[1] > 12) {
		return false;
	}
	if (split.length == 3) {
		if (+split[2] > 31) {
			// todo: check explicit month dates
			return false;
		}
	}

	return true;
}

/**
 * Page load Entrypoint.
 * Code execution starts from here!
 */
function pageLoad(): void {
	// Assign element globals
	ChartEnergyTotal = <HTMLCanvasElement>document?.getElementById("chartEnergyTotal");
	ChartEnergyWind = <HTMLCanvasElement>document?.getElementById("chartEnergyWind");
	ChartEnergySolar = <HTMLCanvasElement>document?.getElementById("chartEnergySolar");
	ChartEnergyNet = <HTMLCanvasElement>document?.getElementById("chartEnergyNet");

	ChartMarket = <HTMLCanvasElement>document?.getElementById("chartMarket");
	HistoryDates = <HTMLElement>document?.getElementById("buttonHistory");
	DateTitle = <HTMLTitleElement>document?.getElementById("dateTitle");

	CarbonCard = <HTMLElement>document?.getElementById("cardCarbon");
	ProfitCard = <HTMLElement>document?.getElementById("cardProfit");

	BidTable = <HTMLTableElement>document?.getElementById("tableBid");
	overlayLoading = <HTMLDivElement>document?.getElementById("overlayLoading");

	ButtonDownload = <HTMLButtonElement>document?.getElementById("buttonDownload");
	ButtonDownload.onclick = download;

	PageType = DateType.Day;

	// Get today
	Today = new Date().toISOString().split("T")[0];

	// Enable all skeletons
	// (also hides canvases and api content)
	skeletons(SkeletonState.Visible, SkeletonType.Energy);
	skeletons(SkeletonState.Visible, SkeletonType.Market);
	skeletons(SkeletonState.Visible, SkeletonType.Dates);

	// Extract date parameter from url
	let urlDate: string | null = null;
	const param = window.location.href.split("?")[1];
	if (param != undefined) {
		// Simple length checks, work out correct date format later
		if (param.length > 13 && param.length < 16) {
			// date is a day
			const dateParam = param.split("date=");
			if (dateParam.length == 2) {
				urlDate = dateParam[1];
				PageType = DateType.Day;
			}
		} else if (param.length > 10 && param.length < 13) {
			// Date is a month
			const dateParam = param.split("date=");
			if (dateParam.length == 2) {
				urlDate = dateParam[1];
				PageType = DateType.Month;
			}
		}
	}

	// Set current url date
	if (urlDate != null) {
		if (ValidateDate(urlDate)) {
			// valid date in url parameters
			PageDate = urlDate;
		} else {
			// invalid page date, show notification and use current date
			PageDate = Today;
			console.error("Invalid date: '" + urlDate + "' Using today's date instead.");
		}
	} else {
		// No page date, use current date.
		// Also set a flag so we just get latest result instead...
		PageDate = Today;
		console.warn("No date given, using today's date '" + PageDate + "'");
	}

	// Send api request for dates
	RequestDates().then((response: Response) => {
		// Check response status, before parsing result
		console.log("Date Response Status:" + response.status);
		const result = response.json();

		result.then((result: unknown) => {
			// Attempt to cast result into expected API result
			if (!ValidateResponse(result, "dates")) {
				console.error("Invalid api response from date endpoint");
				console.error(result);
				return;
			}
			console.log(result);


			// Success, data is real!
			Dates = ProcessData["dates"](result as ResponseRegistry["dates"]);
			CreateDates(Dates);
			skeletons(SkeletonState.Hidden, SkeletonType.Dates);

			// Quick check to see if today is a valid date, and just select
			// today or the closest date this month if urlDate is null.
			let latest: ReportDay | ReportMonth | null = null;
			let foundExact = false;

			for (let i = 0; i < Dates.length; i++) {
				const month = Dates[i];

				if (month.date === PageDate.split("-")[0] + "-" + PageDate.split("-")[1]) {
					console.log("Found selected month in reports.");
					if (PageType == DateType.Month) {
						// found month, and we're in a month mode
						foundExact = true;
						latest = month;
						break;
					}

					for (let j = 0; j < month.days.length; j++) {
						const day = month.days[j];
						if (latest === null) {
							latest = day;
						}
						if (day.date === PageDate) {
							// We found the page date!
							latest = day;
							console.log("Date Found!");
							foundExact = true;
							break;
						}
						if (day.day > latest.day) {
							// Assume time is linear;- largest day is closest
							latest = day;
							continue;
						}
					}
					break;
				}
			}
			if (urlDate == null && !foundExact) {
				if (latest !== null) {
					PageDate = latest.date;
					console.log("No reports for today, so we picked the closest date");
					foundExact = true;
				} else {
					console.error("Unable to find any records for this month.");
				}
			}

			if (foundExact && latest !== null) {
				ChangeDate(latest.date);
			} else {
				console.error("Unable to find given provided date. '" + PageDate + "'");
			}
		}).catch((reason: unknown) => {
			console.error("Unable to parse report dates");
			console.error(response);
			console.error(reason);
			skeletons(SkeletonState.Error, SkeletonType.Dates);
		});
	}).catch((reason: unknown) => {
		console.error("Error requesting report dates");
		console.error(reason);
		skeletons(SkeletonState.Error, SkeletonType.Dates);
	});

	UpdatePage();
}

function markLoading() {
	flagLoading += 1;
	ButtonDownload.setAttribute("loading", "true");
	overlayLoading.classList.add("overlay");
	console.log("markLoading(): " + flagLoading);
}

function markLoaded() {
	flagLoading -= 1;
	console.log("markLoaded(): " + flagLoading);

	if (flagLoading == 0.0) {
		// loaded
		ButtonDownload.removeAttribute("loading");
		overlayLoading.classList.remove("overlay");
	}
}

function download(): void {
	if (flagLoading !== 0) {
		console.error("Data has no yet loaded, cancelling download.");
		return;
	}
	if (HasEnergyData) {
		const energyLink = document.createElement("a");
		energyLink.download = PageDate + ".csv";
		energyLink.href = "api/downloads/energy/" + PageDate;
		energyLink.click();
	}
	if (HasBidData) {
		const bidLink = document.createElement("a");
		bidLink.download = PageDate + ".csv";
		bidLink.href = "api/downloads/bids/" + PageDate;
		bidLink.click();
	}
}

// Start the pageLoad function when the browser window loads.
// This is our entrypoint.
window.onload = pageLoad;
