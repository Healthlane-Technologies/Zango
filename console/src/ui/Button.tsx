import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from 'react';
import { Link, type LinkProps } from 'react-router-dom';
import { cx } from './cx';
import { Icon, type IconName } from './Icon';

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger';
type Size = 'md' | 'sm' | 'xs';

const variantClass: Record<Variant, string> = {
	primary: 'btn-p',
	secondary: 'btn-s',
	ghost: 'btn-g',
	danger: 'btn-d',
};
const sizeClass: Record<Size, string> = { md: '', sm: 'btn-sm', xs: 'btn-xs' };

interface Common {
	variant?: Variant;
	size?: Size;
	icon?: IconName;
	loading?: boolean;
	children?: ReactNode;
}

function content({ icon, loading, children }: Common) {
	return (
		<>
			{loading ? (
				<span className="spin" />
			) : (
				icon && <Icon name={icon} weight={icon === 'plus' ? 2.2 : 1.8} />
			)}
			{children}
		</>
	);
}

export const Button = forwardRef<
	HTMLButtonElement,
	Common & ButtonHTMLAttributes<HTMLButtonElement>
>(function Button(
	{
		variant = 'secondary',
		size = 'md',
		icon,
		loading,
		children,
		className,
		disabled,
		type = 'button',
		...rest
	},
	ref,
) {
	return (
		<button
			ref={ref}
			type={type}
			disabled={disabled || loading}
			className={cx('btn', variantClass[variant], sizeClass[size], className)}
			{...rest}
		>
			{content({ icon, loading, children })}
		</button>
	);
});

export function ButtonLink({
	variant = 'secondary',
	size = 'md',
	icon,
	children,
	className,
	...rest
}: Common & LinkProps) {
	return (
		<Link className={cx('btn', variantClass[variant], sizeClass[size], className)} {...rest}>
			{content({ icon, children })}
		</Link>
	);
}
