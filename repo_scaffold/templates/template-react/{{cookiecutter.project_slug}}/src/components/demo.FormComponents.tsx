{% raw %}import { useStore } from '@tanstack/react-form'

import { useFieldContext, useFormContext } from '#/hooks/demo.form-context'

import MuiButton from '@mui/material/Button'
import MuiTextField from '@mui/material/TextField'
import MenuItem from '@mui/material/MenuItem'
import MuiSlider from '@mui/material/Slider'
import MuiSwitch from '@mui/material/Switch'
import FormControlLabel from '@mui/material/FormControlLabel'
import FormHelperText from '@mui/material/FormHelperText'
import FormControl from '@mui/material/FormControl'
import InputLabel from '@mui/material/InputLabel'
import MuiSelect from '@mui/material/Select'

export function SubscribeButton({ label }: { label: string }) {
  const form = useFormContext()
  return (
    <form.Subscribe selector={(state) => state.isSubmitting}>
      {(isSubmitting) => (
        <MuiButton type="submit" variant="contained" disabled={isSubmitting}>
          {label}
        </Button>
      )}
    </form.Subscribe>
  )
}

function ErrorMessages({
  errors,
}: {
  errors: Array<string | { message: string }>
}) {
  if (errors.length === 0) return null
  return (
    <FormHelperText error>
      {errors.map((error) => (
        <span key={typeof error === 'string' ? error : error.message}>
          {typeof error === 'string' ? error : error.message}
        </span>
      ))}
    </FormHelperText>
  )
}

export function TextField({
  label,
  placeholder,
}: {
  label: string
  placeholder?: string
}) {
  const field = useFieldContext<string>()
  const errors = useStore(field.store, (state) => state.meta.errors)

  return (
    <MuiTextField
      label={label}
      placeholder={placeholder}
      value={field.state.value}
      onBlur={field.handleBlur}
      onChange={(e) => field.handleChange(e.target.value)}
      error={field.state.meta.isTouched && errors.length > 0}
      helperText={field.state.meta.isTouched && <ErrorMessages errors={errors} />}
      fullWidth
      size="small"
    />
  )
}

export function TextArea({
  label,
  rows = 3,
}: {
  label: string
  rows?: number
}) {
  const field = useFieldContext<string>()
  const errors = useStore(field.store, (state) => state.meta.errors)

  return (
    <MuiTextField
      label={label}
      value={field.state.value}
      onBlur={field.handleBlur}
      onChange={(e) => field.handleChange(e.target.value)}
      multiline
      rows={rows}
      error={field.state.meta.isTouched && errors.length > 0}
      helperText={field.state.meta.isTouched && <ErrorMessages errors={errors} />}
      fullWidth
      size="small"
    />
  )
}

export function Select({
  label,
  values,
  placeholder,
}: {
  label: string
  values: Array<{ label: string; value: string }>
  placeholder?: string
}) {
  const field = useFieldContext<string>()
  const errors = useStore(field.store, (state) => state.meta.errors)

  return (
    <FormControl fullWidth size="small" error={field.state.meta.isTouched && errors.length > 0}>
      <InputLabel>{label}</InputLabel>
      <MuiSelect
        value={field.state.value}
        label={label}
        onBlur={field.handleBlur}
        onChange={(e) => field.handleChange(e.target.value)}
      >
        {placeholder && (
          <MenuItem value="" disabled>
            {placeholder}
          </MenuItem>
        )}
        {values.map((value) => (
          <MenuItem key={value.value} value={value.value}>
            {value.label}
          </MenuItem>
        ))}
      </MuiSelect>
      {field.state.meta.isTouched && <ErrorMessages errors={errors} />}
    </FormControl>
  )
}

export function Slider({ label }: { label: string }) {
  const field = useFieldContext<number>()
  const errors = useStore(field.store, (state) => state.meta.errors)

  return (
    <div>
      <FormControlLabel
        control={
          <MuiSlider
            value={field.state.value}
            onChange={(_, value) => field.handleChange(value as number)}
            onBlur={field.handleBlur}
            valueLabelDisplay="auto"
          />
        }
        label={label}
        labelPlacement="top"
      />
      {field.state.meta.isTouched && <ErrorMessages errors={errors} />}
    </div>
  )
}

export function Switch({ label }: { label: string }) {
  const field = useFieldContext<boolean>()
  const errors = useStore(field.store, (state) => state.meta.errors)

  return (
    <div>
      <FormControlLabel
        control={
          <MuiSwitch
            checked={field.state.value}
            onChange={(e) => field.handleChange(e.target.checked)}
            onBlur={field.handleBlur}
          />
        }
        label={label}
      />
      {field.state.meta.isTouched && <ErrorMessages errors={errors} />}
    </div>
  )
}{% endraw %}
