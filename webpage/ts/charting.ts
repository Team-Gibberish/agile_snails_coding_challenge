/**
 * Charting.ts : Charting functions directly linked to charting html divisions.
 * Functions here will directly affect page HTML.
 * @author Iwan Mitchell
 */

// Chart.js does not explicitly use all modules, so they must be registered,
// otherwise vague unhelpful runtime errors will occur...
import { Chart, ChartOptions, Color, Scriptable, ScriptableLineSegmentContext, registerables, ScriptableContext, Tick, Scale } from "chart.js";
Chart.register(...registerables);

import { colors } from "./colors";
import { BidType, DataRegistry } from "./requests";

/**
 * Chart display functions.
 */
export const displayChart = {
	windPower: displayWind,
	solarPower: displaySolar,
	overviewPower: displayOverviewPower,
	netPower: displayNetPower,
	overviewMarket: displayOverviewMarket,
};

/**
 * Default chart options for power graphs.
 */
function DefaultPowerOptions(): ChartOptions {
	return {
		responsive: true,
		maintainAspectRatio: false,
		interaction: {
			mode: "index",
			intersect: false,
		},
		scales: {
			x: {
				axis: "x",
				display: true,
				ticks: {
					display: true,
					callback: tickDate,
				},
				title: {
					display: true,
					text: "Time",
				},
			},
			y: {
				axis: "y",
				display: true,
				suggestedMin: 0,
				ticks: {
					display: true,
				},
				title: {
					display: true,
					text: "kW-h",
				},
			},
		},
	};
}

/**
 * Default dataset options for predicted data in power graphs.
 */
function DefaultPredictedPower(): any {
	return {
		label: "Predicted",
		backgroundColor: colors["red-500"],
		borderColor: colors["red-500"],
		cubicInterpolationMode: "monotone",
		fill: false,
		borderDash: [5, 5],
		radius: 0,
	};
}

/**
 * Default dataset options for real generation data in power graphs.
 */
function DefaultGeneratedPower(): any {
	return {
		label: "Actual",
		backgroundColor: colors["blue-500"],
		borderColor: colors["blue-500"],
		cubicInterpolationMode: "monotone",
		fill: true,
		radius: 0,
	};
}

/**
 * Display tick labels with only the first segment before a space.
 * e.g: 2021-08-01 00:00:00+00:00 as 2021-08-01
 * @param this - Scale element containing ticks
 * @param tickValue - Numeric value of the tick
 * @param index - Index of the tick
 * @param ticks - Array storing ticks for the graph
 * @returns A string, number, or null value with the display string of the tick
 */
function tickDate(this: Scale, tickValue: number | string, index: number, ticks: Tick[]): string | number | null | undefined {
	return (this.getLabelForValue(index) as string).split(" ")[0];
}


/**
 * Create and display a wind generation and prediction chart within the given canvas.
 * @param canvas - Canvas element to generate chart within.
 * @param energyData - Energy data for display.
 */
function displayWind(canvas: HTMLCanvasElement, energyData: DataRegistry["energy"]): void {
	// Destroy any existing chart in the canvas
	Chart.getChart(canvas)?.destroy();

	// Configure global chart settings
	const WindOptions = DefaultPowerOptions();
	WindOptions.plugins = {
		title: {
			display: true,
			text: "Wind Energy Generation"
		}
	};

	// Create and configure dataset settings
	const predictedSettings = DefaultPredictedPower();
	predictedSettings.data = energyData.predictedWindGeneration;

	const generatedSettings = DefaultGeneratedPower();
	generatedSettings.data = energyData.realWindGeneration;
	generatedSettings.backgroundColor = colors["light-blue-300"];
	generatedSettings.borderColor = colors["light-blue-600"];

	// Create chart
	new Chart(canvas, {
		type: "line",
		data: {
			labels: energyData.times,
			datasets: [predictedSettings, generatedSettings],
		},
		options: WindOptions,
	}).update();
}

/**
 * Create and display a solar generation and prediction chart within the given canvas.
 * @param canvas - Canvas element to generate chart within.
 * @param energyData - Energy data for display.
 */
function displaySolar(canvas: HTMLCanvasElement, energyData: DataRegistry["energy"]): void {
	// Destroy any existing chart in the canvas
	Chart.getChart(canvas)?.destroy();

	// Configure global chart settings
	const SolarOptions = DefaultPowerOptions();
	SolarOptions.plugins = {
		title: {
			display: true,
			text: "Solar Energy Generation"
		}
	};

	// Create and configure dataset settings
	const predictedSettings = DefaultPredictedPower();
	predictedSettings.data = energyData.predictedSolarGeneration;

	const generatedSettings = DefaultGeneratedPower();
	generatedSettings.data = energyData.realSolarGeneration;
	generatedSettings.backgroundColor = colors["yellow-500"];
	generatedSettings.borderColor = colors["yellow-600"];

	// Create chart
	new Chart(canvas, {
		type: "line",
		data: {
			labels: energyData.times,
			datasets: [predictedSettings, generatedSettings],
		},
		options: SolarOptions,
	});
}

/**
 * Line option workaround for segment contexts
 */
interface SegmentedLineSettings {
	segment: {
		backgroundColor: Scriptable<Color | undefined, ScriptableLineSegmentContext>,
		borderColor: Scriptable<Color | undefined, ScriptableLineSegmentContext>,
		borderCapStyle: Scriptable<CanvasLineCap | undefined, ScriptableLineSegmentContext>;
		borderDash: Scriptable<number[] | undefined, ScriptableLineSegmentContext>;
		borderDashOffset: Scriptable<number | undefined, ScriptableLineSegmentContext>;
		borderJoinStyle: Scriptable<CanvasLineJoin | undefined, ScriptableLineSegmentContext>;
		borderWidth: Scriptable<number | undefined, ScriptableLineSegmentContext>;
	};
	label: any;
	data: any;
	fill: boolean;
	radius: number,

}

// Colouring functions
const lineNegativeBackgroundLight: Scriptable<Color, ScriptableLineSegmentContext> = (context: ScriptableLineSegmentContext) => context.p1.parsed.y > 0 ? colors["green-200"] : colors["red-200"];
const lineNegativeBackground: Scriptable<Color, ScriptableLineSegmentContext> = (context: ScriptableLineSegmentContext) => context.p1.parsed.y > 0 ? colors["green-500"] : colors["red-500"];
const lineNegativeBorder: Scriptable<Color, ScriptableLineSegmentContext> = (context: ScriptableLineSegmentContext) => context.p1.parsed.y > 0 ? colors["green-500"] : colors["red-600"];
const barNegativeBackground: Scriptable<Color, ScriptableContext<"bar">> = (context: ScriptableContext<"bar">) => context.parsed.y > 0 ? colors["green-500"] : colors["red-500"];
const barNegativeBorder: Scriptable<Color, ScriptableContext<"bar">> = (context: ScriptableContext<"bar">) => context.parsed.y > 0 ? colors["green-500"] : colors["red-600"];

/**
 * Create and display a market overview chart.
 * @param canvas - Canvas element to generate chart within.
 * @param energyData - Energy data for display.
 */
function displayOverviewMarket(canvas: HTMLCanvasElement, bidData: DataRegistry["bids"]): void {
	// Destroy any existing chart in the canvas
	Chart.getChart(canvas)?.destroy();

	// Convert bids into plottable points
	const bidValues: Array<number> = [];
	const bidLabels: Array<string> = [];

	bidData.bids.forEach(bid => {
		bidValues.push(bid.price * bid.volume * (bid.type == BidType.Sell ? 1 : -1));
		bidLabels.push(bid.hour.toString());
	});

	// Create and configure dataset settings
	const bidSettings: any = {
		label: "Bid (£)",
		data: bidValues,
		radius: 0,
		fill: true
	};

	// Create chart
	new Chart(canvas, {
		type: "bar",
		data: {
			labels: bidLabels,
			datasets: [bidSettings],
		},
		options: {
			responsive: true,
			maintainAspectRatio: false,
			interaction: {
				mode: "index",
				intersect: false,
			},
			plugins: {
				title: {
					display: true,
					text: "Market Bid Overview",
				},
				legend: {
					display: false
				},
			},
			elements: {
				bar: {
					borderWidth: 1,
					backgroundColor: barNegativeBackground,
					borderColor: barNegativeBorder,
				}
			},
			scales: {
				x: {
					axis: "x",
					display: true,
					ticks: {
						display: true,
						callback: tickDate,
					},
					title: {
						display: true,
						text: "Time",
					},
				},
				y: {
					axis: "y",
					display: true,
					suggestedMin: 0,
					ticks: {
						display: true,
					},
					title: {
						display: true,
						text: "Bid Amount (£)",
					},
				},
			},
		},
	});
}

/**
 * Create and display a large power overview chart.
 * @param canvas - Canvas element to generate chart within.
 * @param energyData - Energy data for display.
 */
function displayNetPower(canvas: HTMLCanvasElement, energyData: DataRegistry["energy"]): void {
	// Destroy any existing chart in the canvas
	Chart.getChart(canvas)?.destroy();

	// Configure global chart settings
	const OverviewOptions = DefaultPowerOptions();
	OverviewOptions.plugins = {
		title: {
			display: true,
			text: "Net Power Generation"
		},
		legend: {
			display: false,
		}
	};

	// Create and configure dataset settings
	const predictedSettings: SegmentedLineSettings = {
		label: DefaultPredictedPower().label,
		data: energyData.predictedNetGeneration,
		segment: {
			borderColor: lineNegativeBackgroundLight,
			backgroundColor: lineNegativeBackgroundLight,
			borderCapStyle: undefined,
			borderDash: [5, 5],
			borderDashOffset: undefined,
			borderJoinStyle: undefined,
			borderWidth: undefined
		},
		radius: 0,
		fill: true
	};

	const realSettings: SegmentedLineSettings = {
		label: DefaultGeneratedPower().label,
		data: energyData.realNetGeneration,
		radius: 0,
		segment: {
			borderColor: lineNegativeBorder,
			backgroundColor: lineNegativeBackground,
			borderCapStyle: undefined,
			borderDash: undefined,
			borderDashOffset: undefined,
			borderJoinStyle: undefined,
			borderWidth: undefined
		},
		fill: true
	};

	// Create chart
	new Chart(canvas, {
		type: "line",
		data: {
			labels: energyData.times,
			datasets: [realSettings, predictedSettings],
		},
		options: OverviewOptions,
	});
}


/**
 * Create and display a large power overview chart.
 * @param canvas - Canvas element to generate chart within.
 * @param energyData - Energy data for display.
 */
function displayOverviewPower(canvas: HTMLCanvasElement, energyData: DataRegistry["energy"]): void {
	// Destroy any existing chart in the canvas
	Chart.getChart(canvas)?.destroy();

	// Configure global chart settings
	const OverviewOptions = DefaultPowerOptions();
	OverviewOptions.plugins = {
		title: {
			display: true,
			text: "Energy Generation Overview"
		}
	};

	// Create and configure dataset settings
	const predictedSettings = DefaultPredictedPower();
	predictedSettings.data = energyData.predictedTotalGeneration;
	predictedSettings.backgroundColor = colors["green-900"];
	predictedSettings.borderColor = colors["green-900"];
	predictedSettings.radius = 0;

	const generatedSettings = DefaultGeneratedPower();
	generatedSettings.data = energyData.realTotalGeneration;
	generatedSettings.backgroundColor = colors["light-green-400"] + "7F";
	generatedSettings.borderColor = colors["light-green-400"];
	predictedSettings.radius = 0;

	const predictedDemandSettings = DefaultPredictedPower();
	predictedDemandSettings.data = energyData.predictedBuildingDemand;
	predictedDemandSettings.backgroundColor = colors["orange-900"];
	predictedDemandSettings.borderColor = colors["orange-900"];
	predictedDemandSettings.label = "Predicted Usage";

	const realDemandSettings = DefaultGeneratedPower();
	realDemandSettings.data = energyData.realBuildingDemand;
	realDemandSettings.backgroundColor = colors["orange-200"] + "7F";
	realDemandSettings.borderColor = colors["orange-200"];
	realDemandSettings.label = "Actual Usage";


	// Create chart
	new Chart(canvas, {
		type: "line",
		data: {
			labels: energyData.times,
			datasets: [predictedDemandSettings, realDemandSettings, predictedSettings, generatedSettings],
		},
		options: OverviewOptions,
	});
}
