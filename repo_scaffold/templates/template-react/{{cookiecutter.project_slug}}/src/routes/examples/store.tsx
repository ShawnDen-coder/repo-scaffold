{% raw %}
import { createFileRoute } from '@tanstack/react-router'
import { useStore } from '@tanstack/react-store'

import { fullName, store } from '#/lib/store'

export const Route = createFileRoute('/examples/store')({
  component: StoreExample,
})

function FirstName() {
  const firstName = useStore(store, (state) => state.firstName)
  return (
    <input
      type="text"
      value={firstName}
      onChange={(e) =>
        store.setState((state) => ({ ...state, firstName: e.target.value }))
      }
      className="demo-input"
    />
  )
}

function LastName() {
  const lastName = useStore(store, (state) => state.lastName)
  return (
    <input
      type="text"
      value={lastName}
      onChange={(e) =>
        store.setState((state) => ({ ...state, lastName: e.target.value }))
      }
      className="demo-input"
    />
  )
}

function FullName() {
  const fName = useStore(fullName, (state) => state)
  return <div className="demo-list-item font-medium">{fName}</div>
}

function StoreExample() {
  return (
    <main className="demo-page demo-center">
      <section className="demo-panel flex w-full max-w-xl flex-col gap-4">
        <p className="island-kicker">TanStack Store</p>
        <h1 className="demo-title mb-2">Store Example</h1>
        <FirstName />
        <LastName />
        <FullName />
      </section>
    </main>
  )
}
{% endraw %}
