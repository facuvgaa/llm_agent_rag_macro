import './PromoBanner.css'

interface PromoBannerProps {
  onClose: () => void
}

function PromoBanner({ onClose }: PromoBannerProps) {
  return (
    <div className="promo-banner">
      <div className="promo-content">
        <div className="promo-left">
          <div className="promo-icon">
            <svg
              width="20"
              height="20"
              viewBox="0 0 20 20"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M10 2L12.5 7.5L18 8.5L14 12.5L14.5 18L10 15.5L5.5 18L6 12.5L2 8.5L7.5 7.5L10 2Z"
                fill="currentColor"
              />
            </svg>
          </div>
          <div className="promo-text">
            <p className="promo-title">¿Quieres seguir usando GPT-5? Prueba Plus gratis.</p>
            <p className="promo-subtitle">
              Mejora tu plan para seguir obteniendo respuestas más rápidas y mejores.
            </p>
          </div>
        </div>
        <div className="promo-right">
          <button className="promo-button" onClick={() => console.log('Try Plus')}>
            Prueba Plus gratis
          </button>
          <button className="promo-close" onClick={onClose} aria-label="Cerrar">
            <svg
              width="16"
              height="16"
              viewBox="0 0 16 16"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M12 4L4 12M4 4L12 12"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </button>
        </div>
      </div>
    </div>
  )
}

export default PromoBanner
