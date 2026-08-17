import { useTranslation } from 'react-i18next'
import logoImg from '/assets/images/logo.png'

export default function AboutUs() {
  const { t } = useTranslation()

  return (
    <div className="max-w-2xl mx-auto py-8 px-6">
      <div className="text-center mb-8">
        <img src={logoImg} alt="小艺问答助手" className="mx-auto w-14 h-14 rounded-xl object-cover shadow-md mb-4" />
        <h1 className="text-xl font-bold text-[var(--color-text)]">{t('app.name')}</h1>
        <p className="mt-2 text-sm text-[var(--color-text-tertiary)]">{t('about.description')}</p>
      </div>

      <div className="bg-[var(--color-card)] rounded-xl border border-[var(--color-border)] p-6 space-y-6">
        <p className="text-sm text-[var(--color-text-secondary)] leading-relaxed">{t('about.aboutText')}</p>

        <div>
          <h3 className="text-sm font-medium text-[var(--color-text)] mb-3">{t('about.techStack')}</h3>
          <div className="flex flex-wrap gap-2">
            {['React', 'TypeScript', 'Vite', 'FastAPI', 'LangChain', 'PostgreSQL', 'PGVector', 'Redis', 'DashScope', 'HyDE'].map((tech) => (
              <span key={tech} className="px-2.5 py-1 text-xs rounded-full bg-rose-50 dark:bg-rose-900/30 text-rose-500 dark:text-rose-300 font-medium">{tech}</span>
            ))}
          </div>
        </div>

        <div>
          <h3 className="text-sm font-medium text-[var(--color-text)] mb-3">{t('about.features')}</h3>
          <ul className="space-y-2">
            {Object.values(t('about.featureList', { returnObjects: true }) as Record<string, string>).map((text) => (
              <li key={text} className="flex items-center gap-2 text-sm text-[var(--color-text-secondary)]">
                <span className="w-1.5 h-1.5 rounded-full bg-rose-400" />{text}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  )
}