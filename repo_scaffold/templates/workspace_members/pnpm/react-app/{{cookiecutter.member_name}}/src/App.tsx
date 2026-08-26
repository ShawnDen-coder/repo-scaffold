export function App() {
  return (
    <main className="min-h-screen bg-slate-950 p-8 text-slate-100">
      <section className="mx-auto max-w-3xl space-y-4">
        <p className="text-sm font-medium text-cyan-300">{{ cookiecutter.package_name }}</p>
        <h1 className="text-4xl font-bold tracking-tight">React workspace app</h1>
        <p className="text-slate-300">Vite, Tailwind CSS, Biome, and Vitest are ready.</p>
      </section>
    </main>
  );
}
