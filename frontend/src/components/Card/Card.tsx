import React from 'react'
import styles from './Card.module.css'

interface CardProps extends React.HTMLAttributes<HTMLElement> {
  children: React.ReactNode
  className?: string
  as?: 'div' | 'article' | 'section'
}

export function Card({ children, className, as: Comp = 'div', ...rest }: CardProps) {
  return (
    <Comp className={`${styles.card} ${className ?? ''}`.trim()} {...rest}>
      {children}
    </Comp>
  )
}

interface CardTitleProps {
  children: React.ReactNode
}

export function CardTitle({ children }: CardTitleProps) {
  return <h3 className={styles.title}>{children}</h3>
}

interface CardDescriptionProps {
  children: React.ReactNode
}

export function CardDescription({ children }: CardDescriptionProps) {
  return <p className={styles.description}>{children}</p>
}
