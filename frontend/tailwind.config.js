/** @type {import('tailwindcss').Config} */
module.exports = {
	darkMode: ["class"],
	content: [
	"./src/**/*.{js,jsx,ts,tsx}",
	"./public/index.html"
  ],
  theme: {
	extend: {
		borderRadius: {
			lg: 'var(--radius)',
			md: 'calc(var(--radius) - 2px)',
			sm: 'calc(var(--radius) - 4px)',
			// Sky Ride brand radius
			'sr': '16px',
			'sr-sm': '12px'
		},
		colors: {
			// Sky Ride Brand Colors
			'sr-primary': '#152c46',
			'sr-accent': '#4670b5', 
			'sr-black': '#000000',
			'sr-primary-light': 'rgba(21, 44, 70, 0.1)',
			'sr-primary-dark': '#0f1f31',
			'sr-accent-light': 'rgba(70, 112, 181, 0.1)',
			'sr-accent-dark': '#365a96',
			
			// Existing shadcn colors
			background: 'hsl(var(--background))',
			foreground: 'hsl(var(--foreground))',
			card: {
				DEFAULT: 'hsl(var(--card))',
				foreground: 'hsl(var(--card-foreground))'
			},
			popover: {
				DEFAULT: 'hsl(var(--popover))',
				foreground: 'hsl(var(--popover-foreground))'
			},
			primary: {
				DEFAULT: 'hsl(var(--primary))',
				foreground: 'hsl(var(--primary-foreground))'
			},
			secondary: {
				DEFAULT: 'hsl(var(--secondary))',
				foreground: 'hsl(var(--secondary-foreground))'
			},
			muted: {
				DEFAULT: 'hsl(var(--muted))',
				foreground: 'hsl(var(--muted-foreground))'
			},
			accent: {
				DEFAULT: 'hsl(var(--accent))',
				foreground: 'hsl(var(--accent-foreground))'
			},
			destructive: {
				DEFAULT: 'hsl(var(--destructive))',
				foreground: 'hsl(var(--destructive-foreground))'
			},
			border: 'hsl(var(--border))',
			input: 'hsl(var(--input))',
			ring: 'hsl(var(--ring))',
			chart: {
				'1': 'hsl(var(--chart-1))',
				'2': 'hsl(var(--chart-2))',
				'3': 'hsl(var(--chart-3))',
				'4': 'hsl(var(--chart-4))',
				'5': 'hsl(var(--chart-5))'
			}
		},
		fontFamily: {
			'sr': ['Open Sans', 'system-ui', 'sans-serif']
		},
		boxShadow: {
			'sr': '0 8px 24px rgba(21, 44, 70, 0.15)',
			'sr-sm': '0 4px 16px rgba(21, 44, 70, 0.12)'
		},
		keyframes: {
			'accordion-down': {
				from: {
					height: '0'
				},
				to: {
					height: 'var(--radix-accordion-content-height)'
				}
			},
			'accordion-up': {
				from: {
					height: 'var(--radix-accordion-content-height)'
				},
				to: {
					height: '0'
				}
			},
			'sr-pulse': {
				'0%, 100%': {
					transform: 'scale(1)'
				},
				'50%': {
					transform: 'scale(1.02)'
				}
			}
		},
		animation: {
			'accordion-down': 'accordion-down 0.2s ease-out',
			'accordion-up': 'accordion-up 0.2s ease-out',
			'sr-pulse': 'sr-pulse 0.15s ease-in-out'
		}
	}
  },
  plugins: [require("tailwindcss-animate")],
};