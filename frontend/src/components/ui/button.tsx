import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-xl text-sm font-medium transition-[transform,background-color,border-color,color,box-shadow,opacity] duration-200 ease-out focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 active:scale-[0.98] [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default: "border border-primary/30 bg-[linear-gradient(135deg,oklch(0.86_0.13_215),oklch(0.79_0.13_255))] text-primary-foreground shadow-[0_16px_34px_-18px_oklch(0.86_0.13_215_/_0.75)] hover:shadow-[0_22px_40px_-18px_oklch(0.86_0.13_215_/_0.9)]",
        destructive: "border border-destructive/30 bg-[linear-gradient(135deg,oklch(0.72_0.17_25),oklch(0.64_0.18_18))] text-destructive-foreground shadow-[0_14px_32px_-18px_oklch(0.72_0.17_25_/_0.65)] hover:shadow-[0_20px_38px_-18px_oklch(0.72_0.17_25_/_0.82)]",
        outline:
          "border border-input bg-background/70 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)] hover:border-primary/25 hover:bg-accent/70 hover:text-accent-foreground",
        secondary: "border border-white/6 bg-secondary/85 text-secondary-foreground shadow-[inset_0_1px_0_rgba(255,255,255,0.03)] hover:bg-secondary",
        ghost: "hover:bg-accent/70 hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-8 rounded-full px-3 text-xs",
        lg: "h-11 px-8",
        icon: "h-10 w-10 rounded-full",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>, VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp className={cn(buttonVariants({ variant, size, className }))} ref={ref} {...props} />
    );
  },
);
Button.displayName = "Button";

export { Button, buttonVariants };
