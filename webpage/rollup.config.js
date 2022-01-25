import { nodeResolve } from "@rollup/plugin-node-resolve";
import { terser } from "rollup-plugin-terser";

// rollup.config.js
/**
 * @type {import('rollup').RollupOptions}
 */
const configs = [
	{
		input: 'out/index.js',
		output: {
			file: 'js/index.js',
			format: 'cjs',
			name: 'main'
		},
		plugins: [
			nodeResolve(),
			terser({format:{comments:false,semicolons:true}})
		]
	},
];

export default configs;
