import resolve from '@rollup/plugin-node-resolve';
import commonjs from '@rollup/plugin-commonjs';
import replace from '@rollup/plugin-replace';
import esbuild from 'rollup-plugin-esbuild';
export default {
 input: 'src/index.tsx',
 output: {file:'dist/index.js',format:'cjs',exports:'default',sourcemap:false},
 external:['react','react-dom','@decky/ui','@decky/api','react/jsx-runtime'],
 plugins:[
  replace({preventAssignment:true,'process.env.NODE_ENV':JSON.stringify('production')}),
  resolve({browser:true}),
  commonjs(),
  esbuild({target:'es2020',jsx:'automatic',tsconfig:'tsconfig.json',minify:false})
 ]
};
