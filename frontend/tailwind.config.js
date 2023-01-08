/* eslint-disable @typescript-eslint/no-var-requires */
const colors = require('tailwindcss/colors')
const defaultTheme = require('tailwindcss/defaultTheme')

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './lib/**/*.{js,ts,jsx,tsx,mdx}',
    './stories/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', ...defaultTheme.fontFamily.sans],
        mono: ['"Source Code Pro"', ...defaultTheme.fontFamily.mono],
      },
      fontSize: {
        '2xs': ['.625rem', { lineHeight: '.75rem' }],
        md: ['1rem', { lineHeight: '1.5rem' }],
      },
      opacity: {
        'elevation-1': '.05',
        'elevation-2': '.08',
        'elevation-3': '.11',
        'elevation-4': '.12',
        'elevation-5': '.14',
        hover: '.08',
        focus: '.12',
        press: '.12',
        drag: '.16',
        'disabled-container': '.12',
        'disabled-content': '.38',
      },
      margin: {
        50: '.125rem',
        75: '.25rem',
        100: '.5rem',
        200: '.75rem',
        300: '1rem',
        400: '1.5rem',
        500: '2rem',
        600: '2.5rem',
        700: '3rem',
        800: '4rem',
        900: '5rem',
        1000: '6rem',
      },
      padding: {
        50: '.125rem',
        75: '.25rem',
        100: '.5rem',
        200: '.75rem',
        300: '1rem',
        400: '1.5rem',
        500: '2rem',
        600: '2.5rem',
        700: '3rem',
        800: '4rem',
        900: '5rem',
        1000: '6rem',
      },
      spacing: {
        50: '.125rem',
        75: '.25rem',
        100: '.5rem',
        200: '.75rem',
        300: '1rem',
        400: '1.5rem',
        500: '2rem',
        600: '2.5rem',
        700: '3rem',
        800: '4rem',
        900: '5rem',
        1000: '6rem',
      },
      borderRadius: {
        xs: '.25rem',
        sm: '.5rem',
        md: '.75rem',
        lg: '1rem',
        xl: '1.5rem',
      },
    },
    colors: {
      transparent: 'transparent',
      current: 'currentColor',
      black: colors.black,
      white: colors.white,

      primary: colors.cyan[100],
      'on-primary': colors.cyan[800],
      'primary-container': colors.cyan[700],
      'on-primary-container': colors.cyan[50],

      secondary: colors.slate[100],
      'on-secondary': colors.slate[800],
      'secondary-container': colors.slate[700],
      'on-secondary-container': colors.slate[50],

      tertiary: colors.teal[100],
      'on-tertiary': colors.teal[800],
      'tertiary-container': colors.teal[700],
      'on-tertiary-container': colors.teal[50],

      background: colors.neutral[900],
      'on-background': colors.neutral[50],
      surface: colors.neutral[900],
      'on-surface': colors.neutral[50],

      'surface-variant': colors.stone[700],
      'on-surface-variant': colors.stone[100],
      outline: colors.stone[400],
      'outline-variant': colors.stone[700],
    },
  },
  plugins: [],
}
