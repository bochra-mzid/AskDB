import { useState } from 'react';
import { Box, TextField, InputAdornment, IconButton } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';

interface ChatInputProps {
	onSubmit: (message: string) => void;
	loading: boolean;
}

export default function ChatInput({ onSubmit, loading }: ChatInputProps) {
	const [message, setMessage] = useState('');

	const handleSubmit = (e: React.FormEvent) => {
		e.preventDefault();
		if (message.trim() && !loading) {
			onSubmit(message);
			setMessage('');
		}
	};

	const handleKeyDown = (e: React.KeyboardEvent) => {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			handleSubmit(e as unknown as React.FormEvent);
		}
	};

	return (
		<Box
			onSubmit={handleSubmit}
			p={2}
			sx={{
				position: 'sticky',
			}}
		>
			<Box
				sx={{
					maxWidth: '950px',
					margin: '0 auto',
					width: '100%',
				}}
			>
				<TextField
					fullWidth
					multiline
					maxRows={3}
					minRows={1}
					value={message}
					onChange={(e) => setMessage(e.target.value)}
					onKeyDown={handleKeyDown}
					placeholder="Ask a question about your database..."
					variant="outlined"
					slotProps={{
						input: {
							endAdornment: (
								<InputAdornment position="end">
									<IconButton
										onClick={handleSubmit}
										disabled={loading || !message.trim()}
										sx={{
											color: '#667eea',
											'&:disabled': {
												opacity: 0.5,
											},
										}}
									>
										<SendIcon />
									</IconButton>
								</InputAdornment>
							),
						},
					}}
					sx={{
						'& .MuiOutlinedInput-root': {
							backgroundColor: '#FFFFFF1A',
							borderRadius: '12px',
						},
					}}
				/>
			</Box>
		</Box>
	);
}
