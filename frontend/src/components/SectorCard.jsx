import { motion } from 'framer-motion'
import './SectorCard.css'

function SectorCard({ sector, index, onClick }) {
    const cardVariants = {
        hidden: { opacity: 0, y: 50, rotateX: -15 },
        visible: {
            opacity: 1,
            y: 0,
            rotateX: 0,
            transition: {
                delay: index * 0.1,
                duration: 0.6,
                ease: "easeOut"
            }
        }
    }

    return (
        <motion.div
            className="sector-card"
            variants={cardVariants}
            whileHover={{
                y: -15,
                scale: 1.02,
                transition: { duration: 0.3 }
            }}
            whileTap={{ scale: 0.98 }}
            onClick={onClick}
        >
            <div className="card-glow"></div>

            <motion.div
                className="card-icon"
                whileHover={{ scale: 1.2, rotate: 5 }}
                transition={{ duration: 0.3 }}
            >
                {sector.icon.startsWith('/') ? (
                    <img src={sector.icon} alt={sector.title} className="sector-icon-img" />
                ) : (
                    sector.icon
                )}
            </motion.div>

            <h3 className="card-title">{sector.title}</h3>
            <p className="card-subtitle">{sector.subtitle}</p>
            <p className="card-tags">{sector.tags}</p>

            <div className="card-footer">
                <motion.button
                    className="launch-btn"
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                >
                    Launch Demo
                    <span className="btn-icon">→</span>
                </motion.button>
            </div>
        </motion.div>
    )
}

export default SectorCard
