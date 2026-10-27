import { useState } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Layout } from './layouts/Layout'
import { Home } from './pages/Home'
import { Article } from './pages/Article'
import { useDebounce } from './hooks/useDebounce'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      refetchOnWindowFocus: false,
    },
  },
})

function AppInner() {
  const [rawSearch,      setRawSearch]     = useState('')
  const [activeCategory, setCategory]      = useState(null)
  const searchQuery = useDebounce(rawSearch, 380)

  return (
    <Layout
      activeCategory={activeCategory}
      onCategory={setCategory}
      searchQuery={rawSearch}
      onSearch={setRawSearch}
    >
      <Routes>
        <Route
          path="/"
          element={
            <Home
              category={activeCategory}
              searchQuery={searchQuery}
              onCategory={setCategory}
            />
          }
        />
        <Route path="/article/:id" element={<Article />} />
      </Routes>
    </Layout>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <AppInner />
      </BrowserRouter>
    </QueryClientProvider>
  )
}
