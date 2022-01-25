/**
 * Requests.ts : Api data requests and type conversions.
 * @author Iwan Mitchell
 */

import { MonthNames } from "./utils";

const BaseAPI = "api/";

/**
 * Registry containing direct-api transmission responses before conversion to
 * correct types.
 */
export interface ResponseRegistry {
	dates: {
		[month: string]: Array<string>;
	};
	energy: {
		data: Array<Array<number | string | null>>;
		carbonRate: CarbonList;
	};
	bids: {
		data: Array<Array<number | string>>;
	};
}

/**
 * A set of days and their carbon per kilowatt hour.
 */
export type CarbonList = {
	[day: string]: number;
};

/**
 * Registry containing all data formats received from external sources after
 * processing.
 */
export interface DataRegistry {
	dates: ReportMonths;
	energy: EnergyData;
	bids: BidData;
}

/**
 * Represents a response from the backend API, before conversion to useable
 * formats.
 */
export type APIResponse = keyof ResponseRegistry;

/**
 * Type of energy market bid.
 */
export enum BidType {
	/**
	 * This bid is selling power to the grid.
	 */
	Sell = "SELL",
	/**
	 * This bid is buying power from the grid.
	 */
	Buy = "BUY",
}

/**
 * Data representing a valid energy market bid, including volume, price, bid
 * time, etc
 */
export interface Bid {
	/**
	 * Date this bid is for. This is not the submission date.
	 */
	date: string,
	/**
	 * Hour of the day this bid is for. This is not the hour this bid was submitted.
	 */
	hour: number,
	/**
	 * The type of bid. Commonly either BUY or SELL.
	 */
	type: BidType,
	/**
	 * The volume of power in Megawatt-Hours.
	 */
	volume: number,
	/**
	 * The price in GBP (£) per Megawatt-Hours this bid is selling or buying.
	 */
	price: number,
}

/**
 * Represents bids for an entire day. Also contains some commonly used
 * precomputed properties, such as daily profit of submitted bids, and the
 * carbon savings.
 */
export interface BidData {
	/**
	 * List of bids for this day.
	 */
	bids: Array<Bid>;
	/**
	 * Net profit of bids, minus buy orders.
	 */
	profit: number;
	/**
	 * Total volume of power sold by bids.
	 */
	volumeSold: number;
	/**
	 * Total volume of power brought by bids.
	 */
	volumeBrought: number;
	/**
	 * Total volume of power sold and brought by bids.
	 */
	totalVolume: number;
}

/**
 * Energy data obtained from real measurement and predicted values, aligned to
 * the same time and dates.
 */
export interface EnergyData {
	/**
	 * Date/Time of each datapoint.
	 */
	times: Array<string>;
	/**
	 * Predicted building energy demand
	 */
	predictedBuildingDemand: Array<number>;
	/**
	 * Predicted solar energy production.
	 */
	predictedSolarGeneration: Array<number>;
	/**
	 * Predicted wind energy production
	 */
	predictedWindGeneration: Array<number>;
	/**
	 * Real building demand. Null points are for times when data does not exist.
	 * (This may be due to no records, or due to times that haven't happened yet.)
	 */
	realBuildingDemand: Array<number | null>;
	/**
	 * Real solar production. Null points are for times when data does not exist.
	 * (This may be due to no records, or due to times that haven't happened yet.)
	 */
	realSolarGeneration: Array<number | null>;
	/**
	 * Real wind production. Null points are for times when data does not exist.
	 * (This may be due to no records, or due to times that haven't happened yet.)
	 */
	realWindGeneration: Array<number | null>;
	/**
	 * Predicted total energy production. Represents a product of predictedSolar + predictedWind.
	 */
	predictedTotalGeneration: Array<number>;
	/**
	 * Real total energy production. Represents a product of realSolar + realWind.
	 */
	realTotalGeneration: Array<number | null>;
	/**
	 * Predicted amount of net positive energy produced.
	 */
	predictedNetGeneration: Array<number>;
	/**
	 * Real amount of net positive energy produced.
	 */
	realNetGeneration: Array<number | null>;
	/**
	 * Rate of carbon saved per kilowatt hour for each day.
	 */
	carbonRate: CarbonList;
	/**
	 * Predicted net amount of carbon saved for this day.
	 */
	predictedCarbonSaved: number;
	/**
	 * Net amount of carbon saved for this day.
	 */
	realCarbonSaved: number;
}

/**
 * A single day which reporting data exists for.
 */
export interface ReportDay {
	/**
	 * ISO date of day (2021-07-22).
	 */
	date: string;
	/**
	 * Day number.
	 */
	day: number;
}

/**
 * A month of reporting data.
 */
export interface ReportMonth {
	/**
	 * Days with report data.
	 */
	days: Array<ReportDay>;
	/**
	 * Month number (1 = January).
	 */
	month: number;
	/**
	 * Year Number
	 */
	year: number;
	/**
	 * Month Date in ISO format (2021-07).
	 */
	date: string;
	/**
	 * Name of month (January).
	 */
	name: string;
}

/**
 * A full list of months containing reporting data. Months may be from
 * different years.
 */
export type ReportMonths = ReportMonth[];

/**
 * Processing functions for different api datatypes.
 */
export const ProcessData = {
	bids: ProcessBids,
	energy: ProcessEnergy,
	dates: ProcessDates,
};

/**
 * API Endpoints of the backend. Requests taking arguments have a trailing
 * slash.
 */
const APIEndpoints = {
	bids: BaseAPI + "bids/",
	energy: BaseAPI + "report/",
	dates: BaseAPI + "dates",
};

/**
 * Converts raw bidding API responses into formatted and structured bid data for
 * further use.
 *
 * @param data - Bidding Api response.
 * @returns Processed and structured bid data.
 */
export function ProcessBids(data: ResponseRegistry["bids"]): DataRegistry["bids"] {
	const bids: Array<Bid> = [];
	let profit = 0;
	// let carbonRate: number = data.data;
	// let carbonSaved: number = 0;
	let volumeSold = 0;
	let volumeBrought = 0;
	let totalVolume = 0;

	// Create bids
	data.data.forEach(element => {
		const date = element[0] as string;
		const hour = element[1] as number;
		const type = element[2] as BidType;
		const volume = element[3] as number;
		const price = element[4] as number;

		bids.push({
			date: date,
			hour: hour,
			type: type,
			volume: volume,
			price: price,
		});

		// Profit
		profit += volume * price * (type == BidType.Sell ? 1 : -1);

		// Power volume
		totalVolume += volume;
		volumeSold += volume * (type == BidType.Sell ? 1 : 0);
		volumeBrought += volume * (type == BidType.Buy ? 1 : 0);
	});

	return {
		bids: bids,
		profit: profit,
		totalVolume: totalVolume,
		volumeBrought: volumeBrought,
		volumeSold: volumeSold,
	};
}

/**
 * Converts raw energy API responses into formatted and structured bid data for
 * further use.
 * @param data - Energy API response.
 * @returns Processed and structured energy data.
 */
export function ProcessEnergy(data: ResponseRegistry["energy"]): DataRegistry["energy"] {
	// labels
	const dates: Array<string> = [];

	// Predicted data
	const predictedBuildingDemand: Array<number> = [];
	const predictedSolarGeneration: Array<number> = [];
	const predictedWindGeneration: Array<number> = [];
	const predictedTotalGeneration: Array<number> = [];

	// Real data
	const realBuildingDemand: Array<number | null> = [];
	const realSolarGeneration: Array<number | null> = [];
	const realWindGeneration: Array<number | null> = [];
	const realTotalGeneration: Array<number | null> = [];

	// Net power
	const predictedNetPower: Array<number> = [];
	const realNetPower: Array<number | null> = [];

	// Co2
	let predictedCO2 = 0;
	let realCO2 = 0;

	data.data.forEach(element => {
		dates.push(element[0] as string);

		let carbonRate = 0;
		if (typeof element[0] === "string") {
			// 2021-09-02 23:00:00+00:00
			carbonRate = data.carbonRate[element[0].slice(0, 10)];
		}

		predictedBuildingDemand.push(element[1] as number);
		predictedSolarGeneration.push(element[2] as number);
		predictedWindGeneration.push(element[3] as number);
		predictedTotalGeneration.push((element[2] as number) + (element[3] as number));

		const predictedNet = (element[2] as number) + (element[3] as number) - (element[1] as number);
		predictedNetPower.push(predictedNet);
		predictedCO2 += predictedNet * carbonRate;

		realBuildingDemand.push(element[4] as number | null);
		realSolarGeneration.push(element[5] as number | null);
		realWindGeneration.push(element[6] as number | null);

		if (element[5] == null || element[6] == null) {
			// Although one element may be null, we should have real data for
			// both datapoints....
			realTotalGeneration.push(null);
			realNetPower.push(null);
		} else {
			realTotalGeneration.push((element[5] as number) + (element[6] as number));
			if (element[4] !== null) {
				const net = (element[5] as number) + (element[6] as number) - (element[4] as number);
				realNetPower.push(net);
				realCO2 += net * carbonRate;
			} else {
				realNetPower.push(null);
			}
		}
	});


	return {
		times: dates,
		carbonRate: data.carbonRate,

		predictedBuildingDemand: predictedBuildingDemand,
		predictedSolarGeneration: predictedSolarGeneration,
		predictedWindGeneration: predictedWindGeneration,
		predictedTotalGeneration: predictedTotalGeneration,
		predictedNetGeneration: predictedNetPower,
		predictedCarbonSaved: predictedCO2,

		realBuildingDemand: realBuildingDemand,
		realSolarGeneration: realSolarGeneration,
		realWindGeneration: realWindGeneration,
		realTotalGeneration: realTotalGeneration,
		realNetGeneration: realNetPower,
		realCarbonSaved: realCO2,

	};
}

/**
 * Converts raw dates API responses into formatted APIEndpoints structured report dates
 * for further use.
 * @param data - Dates API response.
 * @returns Processed and structured report dates.
 */
export function ProcessDates(data: ResponseRegistry["dates"]): DataRegistry["dates"] {
	const months: ReportMonths = [];

	for (const yearMonth in data) {
		if (Object.prototype.hasOwnProperty.call(data, yearMonth)) {
			const monthDays = data[yearMonth];
			const days: Array<ReportDay> = [];

			// ? Potential issue with parsing strings
			const month: number = Number.parseInt(yearMonth.split("-")[1]);
			const year: number = Number.parseInt(yearMonth.split("-")[0]);

			monthDays.forEach(day => {
				days.push({
					date: yearMonth + "-" + day.toString().padStart(2, "0"),
					day: Number.parseInt(day),
				});
			});
			months.push({
				date: yearMonth,
				days: days,
				month: month,
				name: MonthNames[month - 1],
				year: year,
			});
		}
	}
	return months;
}

/**
 * Request a list of dates with report data from the backend API.
 * @returns A promise of a request from the Dates API. Be sure to Check for
 * invalid and error responses.
 */
export async function RequestDates(): Promise<Response> {
	return await fetch(APIEndpoints.dates);
}

/**
 * Request a list of bids from the backend API.
 * @param date - ISO format (2021-07-22) of a valid date with report data.
 * @returns A promise of a request from the bids API. Be sure to Check for
 * invalid and error responses.
 */
export async function RequestBids(date: string): Promise<Response> {
	return await fetch(APIEndpoints.bids + date);
}

/**
 * Request energy prediction and production from the backend API.
 * @param date - ISO format (2021-07-22) of a valid date with report data.
 * @returns A promise of a request from the energy production API. Be sure to
 * Check for invalid and error responses.
 */
export async function RequestEnergy(date: string): Promise<Response> {
	return await fetch(APIEndpoints.energy + date);
}

/**
 * Validate that the given data is a correctly formatted API response.
 * @param obj - Datatype to Check
 * @param type - Type of API Response
 * @returns Returns True of the given data is a valid APIResponse
 */
export function ValidateResponse(obj: unknown, type: APIResponse): boolean {
	if (typeof obj !== "object") {
		console.error("Response is not an object.");
		return false;
	}
	if (obj == null) {
		console.error("Response is null.");
		return false;
	}

	switch (type) {
	case "bids":
		if (obj["data"] === undefined) {
			// Check to see if bids contains a data key`
			console.error("Bid data field is missing.");
			return false;
		}

		if (!Array.isArray(obj["data"])) {
			// Check to see if bids is an array
			console.error("Bid data field is not an array.");
			return false;
		}

		obj["data"].forEach(element => {
			// Check to ensure elements are also arrays
			if (!Array.isArray(element)) {
				console.error("Bid data array does not contain arrays.");
				return false;
			}
			// Check to ensure elements within arrays are numbers or strings
			element.forEach(element => {
				if (typeof element !== "number" && typeof element !== "string") {
					console.error("Bid data is not numeric or strings.");
					return false;
				}
			});
		});
		return true;
	case "dates":
		for (const key in obj) {
			if (Object.prototype.hasOwnProperty.call(obj, key)) {
				const element = obj[key];
				if (typeof key !== "string") {
					// Ensure all object keys are strings
					console.error("Date keys are not strings.");
					return false;
				}
				if (!Array.isArray(element)) {
					// Ensure all objects are arrays
					console.error("Date values are not arrays.");
					return false;
				}
			}
		}
		return true;
	case "energy":
		if (obj["carbonRate"] === undefined) {
			console.error("Energy carbonRate field is missing.");
			return false;
		}
		if (typeof obj["carbonRate"] !== "object" || obj["carbonRate"] === null) {
			console.error("Energy carbon rate is not an object, or null.");
			return false;
		}
		if (obj["data"] === undefined) {
			// Check to see if energy contains a data key
			console.error("Energy data field is missing.");
			return false;
		}
		for (const key in obj["carbonRate"]) {
			if (Object.prototype.hasOwnProperty.call(obj["carbonRate"], key)) {
				const element = obj["carbonRate"][key];
				if (typeof key !== "string") {
					console.error("Energy carbonRate keys are not strings.");
					return false;
				}
				if (typeof element !== "number" || element == null) {
					console.error("Energy carbonRate values are not numbers, or are null.");
					return false;
				}
			}
		}
		if (!Array.isArray(obj["data"])) {
			// Check to see if data element is an array
			console.error("Energy data field is not an array.");
			return false;
		}
		obj["data"].forEach(element => {
			if (!Array.isArray(element)) {
				// Check to see if all data elements are arrays
				console.error("Energy data array does not contain arrays.");
				return false;
			}
			for (let dataIndex = 0; dataIndex < element.length; dataIndex++) {
				if (dataIndex == 0) {
					if (typeof element[dataIndex] !== "string" && element[dataIndex] != null) {
						// First element in the array is the date string.
						console.error("First element in Energy data array is not a string.");
						return false;
					}
				} else {
					if (typeof element[dataIndex] !== "number" && element[dataIndex] !== null) {
						// Check to see if all other data results are a number, or null
						console.error("Remaining elements in Energy data array are not numbers or null.");
						return false;
					}
				}
			}
		});
		return true;
	default:
		return false;
	}

}

// I Wanted to keep this in :C -- Iwan
// async function RequestAPIData<Type extends keyof typeof ProcessData>(type:Type):Promise<void | ReportDates | EnergyData | Bids> {
// 	return await (async (type: keyof typeof APIEndpoints) => await (await fetch(APIEndpoints[type])).json())(type).then((response:any) => {ProcessData[type](response)});
// }
