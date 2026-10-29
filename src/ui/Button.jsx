import React from 'react';
import './Button.css';

/**
 * Button - A Bootstrap-like React component
 * 
 * @param {Object} props - Component props
 * @param {string} props.children - Button content (text, icon, etc.)
 * @param {string} props.variant - Visual variant: 'primary' (default), 'outline', 'ghost'
 * @param {string} props.size - Button size: 'sm', 'md' (default), 'lg'
 * @param {boolean} props.block - If true, button takes full width
 * @param {boolean} props.loading - If true, shows spinner and disables button
 * @param {boolean} props.disabled - If true, disables button
 * @param {function} props.onClick - Click handler
 * @param {string} props.className - Additional CSS classes
 * @param {string} props.type - Button type: 'button', 'submit', 'reset'
 * @param {React.ReactNode} props.leftIcon - Icon to render on the left
 * @param {React.ReactNode} props.rightIcon - Icon to render on the right
 * @param {object} props.style - Inline styles
 * @param {string} props.id - HTML id attribute
 * @param {string} props.title - Tooltip/title attribute
 * @returns {React.Element} The rendered Button component
 */
const Button = ({
  children,
  variant = 'primary',
  size = 'md',
  block = false,
  loading = false,
  disabled = false,
  onClick,
  className = '',
  type = 'button',
  leftIcon = null,
  rightIcon = null,
  style,
  id,
  title,
  ...rest
}) => {
  const isDisabled = disabled || loading;

  const buttonClasses = [
    'btn',
    `btn-${variant}`,
    size !== 'md' && `btn-${size}`,
    block && 'btn-block',
    loading && 'btn-loading',
    className,
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <button
      id={id}
      type={type}
      className={buttonClasses}
      disabled={isDisabled}
      onClick={onClick}
      style={style}
      title={title}
      {...rest}
    >
      {loading && (
        <span className="btn-spinner" aria-hidden="true">
          <span className="sr-only">Loading</span>
        </span>
      )}
      {!loading && leftIcon && (
        <span className="btn-icon btn-icon-left" aria-hidden="true">
          {leftIcon}
        </span>
      )}
      <span className="btn-text">{children}</span>
      {!loading && rightIcon && (
        <span className="btn-icon btn-icon-right" aria-hidden="true">
          {rightIcon}
        </span>
      )}
    </button>
  );
};

export default Button;