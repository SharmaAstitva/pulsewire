import { Navbar } from '../components/Navbar'
import { Footer } from '../components/Footer'

export function Layout({ children, activeCategory, onCategory, searchQuery, onSearch }) {
  return (
    <div className="min-h-screen flex flex-col bg-white">
      <Navbar
        activeCategory={activeCategory}
        onCategory={onCategory}
        searchQuery={searchQuery}
        onSearch={onSearch}
      />
      <main className="flex-1">
        {children}
      </main>
      <Footer />
    </div>
  )
}
